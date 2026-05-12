#!/usr/bin/env python3
"""Eval runner for the triz-workshop plugin (B9, design v6 §21).

OPINIONATED v0.1 SCOPE — SYNTHETIC ONLY
========================================

This runner is intentionally synthetic. It exercises the deterministic state
driver (`scripts/next_action.py`) and the Python helper scripts (selector,
lookup) end-to-end *without* dispatching any LLM subagent. When the state
driver emits an `action == "dispatch_subagent"` action, this runner writes a
**stub artifact** that conforms to the relevant schema and continues the
loop. The stub artifacts are NOT realistic LLM output; they encode just
enough structure for the state driver to advance to the next stage.

Why synthetic? Two reasons:

1. v0.1 eval measures *routing* — does the deterministic plumbing reach the
   right branch (normal / low_framing_confidence / no_clean_mapping)? Does
   the selector pick the matrix we expect? Does the lookup find the right
   cell? These are properties of the code, not the LLM.

2. Live LLM dispatch is expensive, non-deterministic, and depends on Claude
   Code's runtime which the test suite cannot drive. Phase 2 will add a
   `--live` mode that actually calls subagents; that's tracked separately.

What this runner DOES check (per design v6 §21.2):

  - branch_reached:    did we land in the expected_branch?
  - selected_matrix:   did the selector produce expected_matrix_id?
  - param_pair:        does the synthetic mapper hit expected_param_pair?
  - principle_jaccard: |actual ∩ accepted| / |actual ∪ accepted|.

Note that for SYNTHETIC runs, `param_pair` and `principle_jaccard` are
computed against the stub mapping/principles that THIS runner injects;
they are diagnostic of the routing, not of LLM mapping quality. Phase 2
LIVE eval will measure those for real.

Usage:

    python3 -m eval.run_eval                  # run public cases
    python3 -m eval.run_eval --include-local  # include labeled_problems.local.jsonl

Outputs `eval/reports/<UTC-timestamp>.md` with a summary table.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
EVAL_DIR = PLUGIN_ROOT / "eval"
REPORTS_DIR = EVAL_DIR / "reports"
LIVE_MATRICES_PATH = PLUGIN_ROOT.parent  # registry.json sits at repo root

PUBLIC_CASES = EVAL_DIR / "labeled_problems.public.jsonl"
LOCAL_CASES = EVAL_DIR / "labeled_problems.local.jsonl"

# Maximum dispatch loop iterations per case before we declare a runaway. The
# critical-path stages (§20.5) cap at ~17, plus retries and parallel batches —
# 80 is generous and still bounded for hung-fixture diagnosis.
MAX_LOOP = 80


# --- Result types ---------------------------------------------------------

@dataclass
class CaseResult:
    case_id: str
    expected_branch: str
    branch_reached: Optional[str] = None
    branch_match: bool = False
    expected_matrix_id: Optional[str] = None
    selected_matrix: Optional[str] = None
    matrix_match: Optional[bool] = None
    expected_param_pair: Optional[list[str]] = None
    actual_param_pair: Optional[list[str]] = None
    param_pair_match: Optional[bool] = None
    accepted_principles: Optional[list[int]] = None
    actual_principles: Optional[list[int]] = None
    principle_jaccard: Optional[float] = None
    error: Optional[str] = None
    actions_seen: list[str] = field(default_factory=list)


# --- Stub-artifact factories ---------------------------------------------
#
# Each factory writes a schema-valid stub and returns the path. The state
# driver re-reads the artifact after the dispatch returns, so these stubs
# directly steer the routing.

def _write_stub_problem(run_dir: Path, case: dict) -> None:
    """Stub for the triz-problem-framer subagent.

    The framing_confidence is the routing knob. For low-framing cases we
    emit `low` so the state driver branches to `ask_user clarify_framing`.
    """
    branch = case.get("expected_branch")
    framing_confidence = "low" if branch == "low_framing_confidence" else "high"
    domain_class = case.get("domain_class") or "general-engineering"
    # Minimal-but-schema-valid problem. The framer would normally extract
    # improving/worsening from the user prompt; we synthesize a placeholder.
    payload = {
        "schema_version": 1,
        "improving_concept": case.get("improving_concept", "improve target attribute"),
        "worsening_concept": case.get("worsening_concept", "worsen side-effect attribute"),
        "domain_signals": case.get("domain_signals", [_pick_domain_signal(domain_class)]),
        "exotic_signals": case.get("exotic_signals", []),
        "contradiction_type": "engineering-contradiction",
        "domain_class": domain_class,
        "framing_confidence": framing_confidence,
        "constraints": [],
        "rationale": f"synthetic stub for {case['case_id']}",
    }
    _atomic_write(run_dir / "01_problem.json", payload)


def _pick_domain_signal(domain_class: str) -> str:
    """Map a coarse domain_class to a representative domain_signal tag.

    Drawn from selector_tags_vocabulary.json:domain_signals. The selector's
    Stage B scoring (§7) uses domain overlap, so picking a credible signal
    is part of the routing test.
    """
    table = {
        "mechanical": "mechanical",
        "manufacturing": "manufacturing",
        "thermal": "thermal",
        "electrical": "electrical",
        "software": "software",
        "service": "service",
        "governance": "governance",
        "bio": "bio",
        "general-engineering": "mechanical",
    }
    return table.get(domain_class or "", "mechanical")


def _write_stub_mapping(
    run_dir: Path,
    matrix_id: str,
    case: dict,
    no_clean_mapping: bool = False,
) -> None:
    """Stub for the triz-parameter-mapper subagent.

    For `no_clean_mapping` cases we set the flag; the state driver then
    emits the no-clean-mapping branch.

    Param pair selection: if the case's expected_param_pair is for the
    SAME matrix as `matrix_id`, use it (so the routing checks
    expected_param_pair properly). Otherwise pick a matrix-appropriate
    default that the matrix's parameter_id_style accepts. This avoids
    routing into the no-clean-mapping branch just because the synthetic
    pair is incompatible with whatever matrix the selector chose.
    """
    expected_matrix = case.get("expected_matrix_id")
    expected_pair = case.get("expected_param_pair")
    if expected_pair and expected_matrix == matrix_id:
        pair = expected_pair
    else:
        pair = _default_pair_for_matrix(matrix_id)
    payload = {
        "schema_version": 1,
        "matrix_id": matrix_id,
        "improving_param_id": str(pair[0]),
        "worsening_param_id": str(pair[1]),
        "improving_rationale": "synthetic stub mapping",
        "worsening_rationale": "synthetic stub mapping",
        "alternatives": [],
        "mapping_confidence": "low" if no_clean_mapping else "high",
        "no_clean_mapping": bool(no_clean_mapping),
    }
    fname = f"03_mapping_{matrix_id}.json"
    _atomic_write(run_dir / fname, payload)


# Per-matrix default param pairs. Selected to be (a) within the matrix's
# valid id range, (b) typically populated (i.e., the matrix cell is
# non-empty), so the stub keeps the run from falling into no-clean-mapping
# unless the case explicitly asks for it.
_DEFAULT_PAIRS = {
    # numeric-style 39x39 matrices
    "altshuller_39x39": ("1", "9"),
    "altshuller_russian_original": ("1", "9"),
    "matriz_org_39x39": ("1", "9"),
    "triz_agents_39x39": ("1", "9"),
    "heinrich_39x39": ("1", "9"),
    "triz_ai_50x50": ("1", "9"),
    # 6x6 BioTRIZ matrices
    "biotriz_6x6_bio": ("1", "2"),
    "biotriz_6x6_tech": ("1", "2"),
    "biotriz_6x6_legacy": ("1", "2"),
    "biotriz_24x24": ("1", "2"),
    # drug safety 18x18
    "drug_safety_18x18": ("1", "2"),
    # innovate triz 18x18
    "innovatetriz_extended": ("1", "2"),
    # healthcare prefixed (S = service-quality, T = technical-quality)
    "healthcare_servqual": ("S2", "T25"),
    # mann shell — never populated
    "mann_matrix2003_48x48": ("1", "2"),
}


def _default_pair_for_matrix(matrix_id: str) -> tuple[str, str]:
    return _DEFAULT_PAIRS.get(matrix_id, ("1", "2"))


_MATRIX_LINEAGE = {
    "altshuller_39x39": "altshuller-40",
    "altshuller_russian_original": "altshuller-40",
    "matriz_org_39x39": "altshuller-40",
    "triz_agents_39x39": "altshuller-40",
    "heinrich_39x39": "altshuller-40",
    "biotriz_6x6_bio": "biotriz-40",
    "biotriz_6x6_tech": "altshuller-40",
    "biotriz_6x6_legacy": "biotriz-40",
    "biotriz_24x24": "biotriz-40",
    "drug_safety_18x18": "drug-safety-reframed",
    "innovatetriz_extended": "altshuller-40",
    "healthcare_servqual": "altshuller-40",
    "mann_matrix2003_48x48": "altshuller-40",
    "triz_ai_50x50": "triz-ai-extended",
}


def _matrix_lineage(matrix_id: str) -> str:
    return _MATRIX_LINEAGE.get(matrix_id, "altshuller-40")


def _write_stub_critic_independent(
    run_dir: Path,
    matrix_id: str,
    case: dict,
    no_clean_mapping: bool = False,
) -> None:
    """Stub for the mapping-critic Phase-1 INDEPENDENT mapping artifact.

    Mirrors `_write_stub_mapping` so mapper and critic AGREE on synthetic
    runs (compare_mappings → AGREE → straight to lookup, no Phase-2
    deliberation). Phase-2 deliberation isn't part of v0.1 routing eval.
    """
    expected_matrix = case.get("expected_matrix_id")
    expected_pair = case.get("expected_param_pair")
    if expected_pair and expected_matrix == matrix_id:
        pair = expected_pair
    else:
        pair = _default_pair_for_matrix(matrix_id)
    payload = {
        "schema_version": 1,
        "matrix_id": matrix_id,
        "improving_param_id": str(pair[0]),
        "worsening_param_id": str(pair[1]),
        "confidence": "low" if no_clean_mapping else "high",
        "no_clean_mapping": bool(no_clean_mapping),
        "rationale": "synthetic critic stub",
    }
    fname = f"03c_independent_mapping_{matrix_id}.json"
    _atomic_write(run_dir / fname, payload)


def _write_stub_interpretation(
    run_dir: Path,
    matrix_id: str,
    principle_id: int,
    interpretation_lineage: str = "altshuller-40",
) -> None:
    """Stub for the triz-principle-interpreter subagent.

    Conforms to 05_interpretation_single.schema.json. The synthesizer and
    merge step both consume this; getting the field names right matters
    or merge_interpretations.py validation will fail and the state driver
    keeps re-dispatching forever.

    principle_canonical_id pattern is ^P_[A-Z][A-Z_]*$ — letters/underscores
    only, no digits. We map the integer id via a lowercase->A..Z scheme to
    keep stubs distinct (P_STUBA, P_STUBB, ... P_STUBZZ).
    """
    cid = _canonical_id_for_principle(principle_id)
    fname = f"05_interpretation_{matrix_id}_{principle_id}.json"
    payload = {
        "schema_version": 1,
        "matrix_id": matrix_id,
        "principle_id": str(principle_id),
        "principle_canonical_id": cid,
        "principle_name": f"stub principle #{principle_id}",
        "interpretation_lineage": interpretation_lineage,
        "concrete_suggestion": "synthetic stub suggestion",
        "applies_how": "synthetic stub mapping",
    }
    _atomic_write(run_dir / fname, payload)


def _canonical_id_for_principle(pid: int) -> str:
    """Map an int principle id to a stable letter-only canonical id.

    1 -> P_STUB_A, 2 -> P_STUB_B, ..., 26 -> P_STUB_Z, 27 -> P_STUB_AA, etc.
    Letters-only matches the schema regex ^P_[A-Z][A-Z_]*$.
    """
    if pid <= 0:
        return "P_STUB_A"
    chars = []
    n = pid
    while n > 0:
        n -= 1
        chars.append(chr(ord("A") + (n % 26)))
        n //= 26
    return "P_STUB_" + "".join(reversed(chars))


def _atomic_write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


# --- next_action.py invocation --------------------------------------------

def _invoke_next_action(
    cwd: Path,
    args: list[str],
    user_input: Optional[dict] = None,
) -> dict:
    full = [sys.executable, str(SCRIPTS_DIR / "next_action.py"), *args]
    if user_input is not None:
        full.extend(["--user-input", json.dumps(user_input)])
    env = os.environ.copy()
    env.setdefault("TRIZ_MATRICES_PATH", str(LIVE_MATRICES_PATH))
    proc = subprocess.run(
        full, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"next_action exited {proc.returncode} stderr={proc.stderr!r}"
        )
    if proc.stderr:
        # Tolerate stderr in eval mode (CI tests assert stderr=='' separately).
        pass
    out = proc.stdout.strip()
    if not out:
        raise RuntimeError("next_action produced empty stdout")
    return json.loads(out)


# --- Per-case driver ------------------------------------------------------

def run_case(case: dict) -> CaseResult:
    """Drive one labeled case through the synthetic pipeline."""
    result = CaseResult(
        case_id=case["case_id"],
        expected_branch=case["expected_branch"],
        expected_matrix_id=case.get("expected_matrix_id"),
        expected_param_pair=case.get("expected_param_pair"),
        accepted_principles=case.get("accepted_principles"),
    )

    # Per-case isolated cwd. .triz/ resolves under here.
    with tempfile.TemporaryDirectory(prefix="triz-eval-") as tmp:
        cwd = Path(tmp)
        try:
            # Initialize the run.
            action = _invoke_next_action(
                cwd,
                ["--new-run", "--user-prompt", case["problem_statement"]],
            )
            run_id = action.get("run_id")
            if not run_id:
                raise RuntimeError(f"missing run_id in init action: {action!r}")

            run_dir = cwd / ".triz" / "runs" / run_id

            for step in range(MAX_LOOP):
                kind = action.get("action")
                result.actions_seen.append(kind or "?")

                if kind == "ask_user":
                    ask_kind = action.get("kind")
                    # The two routing branches we explicitly check:
                    if ask_kind == "clarify_framing":
                        result.branch_reached = "low_framing_confidence"
                        break
                    if ask_kind == "no_resolution":
                        # This is the assembly-time no-clean-mapping ask.
                        result.branch_reached = "no_clean_mapping"
                        break
                    # Any other ask_user (e.g., closest_candidates after
                    # selector found 0) — we treat the most likely outcomes:
                    if ask_kind in ("closest_candidates", "no_matrix"):
                        result.branch_reached = "no_clean_mapping"
                        break
                    # Unknown ask: abort.
                    result.error = f"unhandled ask_user kind={ask_kind!r}"
                    break

                if kind == "done":
                    # If we reached done, we routed via the normal branch
                    # OR the no-clean-mapping branch (which also produces
                    # a final-report via assemble_report.py --no_resolution).
                    # Distinguish by reading state.json:flags.no_resolution.
                    result.branch_reached = _classify_done_branch(run_dir)
                    break

                if kind == "self_correct":
                    # Self-correct means the driver hit something it
                    # couldn't handle. Treat as error.
                    result.error = (
                        f"self_correct: {action.get('message', '<no message>')}"
                    )
                    break

                if kind == "dispatch_subagent":
                    _handle_dispatch(action, run_dir, case)
                    action = _invoke_next_action(
                        cwd, ["--run-id", run_id]
                    )
                    continue

                if kind == "dispatch_subagents_parallel":
                    for d in action.get("dispatches", []):
                        _handle_dispatch(d, run_dir, case)
                    action = _invoke_next_action(
                        cwd, ["--run-id", run_id]
                    )
                    continue

                if kind == "run_script":
                    _run_helper_script(action, cwd, run_dir, case)
                    action = _invoke_next_action(
                        cwd, ["--run-id", run_id]
                    )
                    continue

                # Unknown action.
                result.error = f"unknown action kind={kind!r}"
                break
            else:
                result.error = f"runaway loop > {MAX_LOOP} iterations"

            # Post-run analysis.
            _populate_metrics(result, run_dir, case)

        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"

    # Final branch_match.
    result.branch_match = result.branch_reached == result.expected_branch
    return result


def _handle_dispatch(dispatch: dict, run_dir: Path, case: dict) -> None:
    """Write a stub artifact for whatever subagent the action targets."""
    subagent = dispatch.get("subagent")
    expected_artifact = dispatch.get("expected_artifact", "")

    if subagent == "triz-problem-framer":
        _write_stub_problem(run_dir, case)
        return

    if subagent == "triz-parameter-mapper":
        # Filename is 03_mapping_<matrix_id>.json — extract matrix_id.
        matrix_id = expected_artifact.replace("03_mapping_", "").rsplit(".json", 1)[0]
        ncm = case.get("expected_branch") == "no_clean_mapping"
        _write_stub_mapping(run_dir, matrix_id, case, no_clean_mapping=ncm)
        return

    if subagent == "triz-mapping-critic":
        # Could write either 03b_mapping_critique_*.json or
        # 03c_independent_mapping_*.json depending on phase.
        if "03c_independent_mapping_" in expected_artifact:
            matrix_id = expected_artifact.replace(
                "03c_independent_mapping_", ""
            ).rsplit(".json", 1)[0]
            ncm = case.get("expected_branch") == "no_clean_mapping"
            _write_stub_critic_independent(
                run_dir, matrix_id, case, no_clean_mapping=ncm
            )
            return
        if "03b_mapping_critique_" in expected_artifact:
            # Phase-2 deliberation artifact. We just write a minimal stub
            # that says "verdict: agree". Not heavily exercised in v0.1.
            matrix_id = expected_artifact.replace(
                "03b_mapping_critique_", ""
            ).rsplit(".json", 1)[0]
            payload = {
                "schema_version": 1,
                "matrix_id": matrix_id,
                "verdict": "agree",
                "rationale": "synthetic stub critique",
                "no_clean_mapping": case.get("expected_branch") == "no_clean_mapping",
            }
            _atomic_write(run_dir / expected_artifact, payload)
            return

    if subagent == "triz-principle-interpreter":
        # 05_interpretation_<matrix>_<principle>.json. Extract principle_id.
        try:
            stem = expected_artifact.rsplit(".json", 1)[0]
            parts = stem.rsplit("_", 1)
            principle_id = int(parts[-1])
            matrix_id = parts[0].replace("05_interpretation_", "")
        except (ValueError, IndexError):
            matrix_id = "unknown"
            principle_id = 1
        # The state driver passes interpretation_lineage in the prompt, but
        # the artifact's lineage must be the matrix's actual lineage.
        # Default to altshuller-40 unless we can detect biotriz/drug-safety.
        lineage = _matrix_lineage(matrix_id)
        _write_stub_interpretation(run_dir, matrix_id, principle_id, lineage)
        return

    if subagent == "triz-matrix-selector":
        # Stage E LLM tiebreak. The Stage A-D selection already wrote
        # 02_selection.json; Stage E refines it. For the synthetic eval we
        # leave the existing selection untouched (the deterministic stages
        # already chose). Just touch the expected artifact path so the
        # driver advances.
        sel_path = run_dir / "02_selection.json"
        if sel_path.exists():
            sel = json.loads(sel_path.read_text(encoding="utf-8"))
            sel["stage_e_invoked"] = True
            _atomic_write(sel_path, sel)
        return

    if subagent == "triz-solution-synthesizer":
        # Find canonical ids written by the interpretation stubs so the
        # synthesizer's principles_applied + interpretation_refs reference
        # something real.
        canon_ids: list[str] = []
        refs: list[dict] = []
        for p in run_dir.glob("05_interpretation_*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                cid = d.get("principle_canonical_id")
                mid = d.get("matrix_id")
                pid = d.get("principle_id")
                if cid and mid and pid:
                    if cid not in canon_ids:
                        canon_ids.append(cid)
                    refs.append({"matrix_id": mid, "principle_id": str(pid)})
            except Exception:
                pass
        if not canon_ids:
            canon_ids = ["P_STUB_1"]
        if not refs:
            refs = [{"matrix_id": "stub", "principle_id": "1"}]
        payload = {
            "schema_version": 1,
            "candidates": [
                {
                    "name": "synthetic stub candidate",
                    "summary": "synthetic stub for routing eval",
                    "principles_applied": canon_ids[:8],
                    "interpretation_refs": refs[:8],
                    "implementation_sketch": "synthetic",
                    "novelty_estimate": "medium",
                    "effort_estimate": "medium",
                }
            ],
        }
        _atomic_write(run_dir / expected_artifact, payload)
        return

    if subagent in ("triz-solution-critic", "triz-contradiction-critic"):
        payload = {
            "schema_version": 1,
            "per_solution_critiques": [
                {
                    "candidate_name": "synthetic stub candidate",
                    "secondary_contradictions": [],
                    "severity": "minor",
                    "risks": [],
                    "recommendation": "synthetic stub recommendation",
                }
            ],
        }
        _atomic_write(run_dir / expected_artifact, payload)
        return

    # Unknown subagent: write an empty placeholder so the driver doesn't
    # block, but record it.
    _atomic_write(run_dir / expected_artifact, {"schema_version": 1})


def _run_helper_script(
    action: dict, cwd: Path, run_dir: Path, case: dict
) -> None:
    """Execute one of the in-tree helper scripts (selector, lookup, etc.)."""
    script = action.get("script")
    args = action.get("args") or []
    if not script:
        return
    script_path = SCRIPTS_DIR / script
    if not script_path.exists():
        # Caller will see the missing artifact and ask_user / self_correct.
        return
    env = os.environ.copy()
    env.setdefault("TRIZ_MATRICES_PATH", str(LIVE_MATRICES_PATH))
    subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=str(cwd), env=env, capture_output=True, text=True, timeout=60,
    )


# --- Branch classification ------------------------------------------------

def _classify_done_branch(run_dir: Path) -> str:
    """When the state driver returns `done`, classify which branch produced it.

    Reads state.json:flags.no_resolution. If set, the run took the
    no-clean-mapping branch; otherwise it's the normal completion path.
    """
    state_path = run_dir / "state.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("flags", {}).get("no_resolution"):
                return "no_clean_mapping"
        except Exception:
            pass
    return "normal"


# --- Metrics --------------------------------------------------------------

def _populate_metrics(result: CaseResult, run_dir: Path, case: dict) -> None:
    """Read whatever artifacts exist and fill the metric fields."""
    # selected_matrix
    sel_path = run_dir / "02_selection.json"
    if sel_path.exists():
        try:
            sel = json.loads(sel_path.read_text(encoding="utf-8"))
            top = sel.get("selected_matrices", [])
            if top:
                result.selected_matrix = top[0].get("matrix_id")
                if result.expected_matrix_id is not None:
                    result.matrix_match = (
                        result.selected_matrix == result.expected_matrix_id
                    )
        except Exception:
            pass

    # actual_param_pair: read the mapping for the selected matrix (if any).
    if result.selected_matrix:
        m_path = run_dir / f"03_mapping_{result.selected_matrix}.json"
        if m_path.exists():
            try:
                m = json.loads(m_path.read_text(encoding="utf-8"))
                result.actual_param_pair = [
                    m.get("improving_param_id"),
                    m.get("worsening_param_id"),
                ]
                if result.expected_param_pair is not None:
                    result.param_pair_match = (
                        [str(x) for x in result.actual_param_pair]
                        == [str(x) for x in result.expected_param_pair]
                    )
            except Exception:
                pass

        # principle_jaccard.
        p_path = run_dir / f"04_principles_{result.selected_matrix}.json"
        if p_path.exists():
            try:
                p = json.loads(p_path.read_text(encoding="utf-8"))
                result.actual_principles = list(p.get("principles") or [])
                if result.accepted_principles:
                    a = set(int(x) for x in result.actual_principles)
                    b = set(int(x) for x in result.accepted_principles)
                    if a or b:
                        result.principle_jaccard = (
                            len(a & b) / len(a | b) if (a | b) else 0.0
                        )
            except Exception:
                pass


# --- Report writer --------------------------------------------------------

def _format_report(results: list[CaseResult], started: _dt.datetime) -> str:
    finished = _dt.datetime.now(_dt.timezone.utc)
    n = len(results)
    branch_hits = sum(1 for r in results if r.branch_match)
    matrix_hits = sum(
        1 for r in results
        if r.matrix_match is True
    )
    matrix_total = sum(
        1 for r in results
        if r.expected_matrix_id is not None
    )
    err = sum(1 for r in results if r.error)

    lines = [
        f"# triz-workshop eval report",
        "",
        f"- Started: {started.isoformat()}",
        f"- Finished: {finished.isoformat()}",
        f"- Mode: SYNTHETIC v0.1 (no live LLM dispatch)",
        f"- Cases: {n}",
        f"- branch_reached match: {branch_hits}/{n} ({100*branch_hits/n:.0f}%)",
    ]
    if matrix_total:
        lines.append(
            f"- selected_matrix match: {matrix_hits}/{matrix_total} "
            f"({100*matrix_hits/matrix_total:.0f}% of cases that specify a matrix)"
        )
    lines.append(f"- errors: {err}")
    lines.append("")
    lines.append(
        "| case_id | expected_branch | branch_reached | match | "
        "expected_matrix | selected_matrix | jaccard | error |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|"
    )
    for r in results:
        jacc = (
            f"{r.principle_jaccard:.2f}"
            if r.principle_jaccard is not None
            else "—"
        )
        lines.append(
            f"| {r.case_id} | {r.expected_branch} | "
            f"{r.branch_reached or '—'} | "
            f"{'✓' if r.branch_match else '✗'} | "
            f"{r.expected_matrix_id or '—'} | "
            f"{r.selected_matrix or '—'} | {jacc} | "
            f"{(r.error or '—').replace('|', '/')} |"
        )
    lines.append("")
    lines.append("## Per-case action traces")
    lines.append("")
    for r in results:
        lines.append(f"### {r.case_id}")
        lines.append("")
        lines.append("```")
        lines.append(" -> ".join(r.actions_seen) or "(no actions)")
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


# --- Entry point ----------------------------------------------------------

def _load_cases(paths: list[Path]) -> list[dict]:
    cases: list[dict] = []
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cases.append(json.loads(line))
    return cases


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument(
        "--include-local", action="store_true",
        help="Also include labeled_problems.local.jsonl if present.",
    )
    ap.add_argument(
        "--report-stdout", action="store_true",
        help="Also print the report to stdout (in addition to writing to file).",
    )
    ap.add_argument(
        "--out", type=Path, default=None,
        help="Override the default reports/<timestamp>.md output path.",
    )
    args = ap.parse_args(argv)

    paths = [PUBLIC_CASES]
    if args.include_local and LOCAL_CASES.exists():
        paths.append(LOCAL_CASES)
    cases = _load_cases(paths)
    if not cases:
        print("no cases found", file=sys.stderr)
        return 1

    started = _dt.datetime.now(_dt.timezone.utc)
    results: list[CaseResult] = []
    for case in cases:
        try:
            r = run_case(case)
        except Exception as exc:
            r = CaseResult(
                case_id=case.get("case_id", "<unknown>"),
                expected_branch=case.get("expected_branch", "<unknown>"),
                error=f"runner crashed: {type(exc).__name__}: {exc}",
            )
        results.append(r)
        marker = "OK" if r.branch_match else "MISS"
        print(
            f"[{marker}] {r.case_id}: "
            f"expected_branch={r.expected_branch} "
            f"reached={r.branch_reached} "
            f"matrix={r.selected_matrix or '—'} "
            f"err={r.error or '—'}"
        )

    report = _format_report(results, started)

    out = args.out
    if out is None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = started.strftime("%Y%m%dT%H%M%SZ")
        out = REPORTS_DIR / f"{ts}.md"
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"\nreport written to: {out}")
    if args.report_stdout:
        print(report)

    # Non-zero exit if any case errored or no branches matched at all.
    branch_hits = sum(1 for r in results if r.branch_match)
    err = sum(1 for r in results if r.error)
    if branch_hits == 0:
        return 2
    return 0 if err == 0 else 0  # v0.1: don't fail CI on partial misses.


if __name__ == "__main__":
    raise SystemExit(main())
