#!/usr/bin/env python3
"""select_matrix.py — Stages A-D of matrix selection per design v6 §14.

Reads:
    .triz/runs/<run-id>/01_problem.json
    registry.json + use_cases/*.json

Writes:
    .triz/runs/<run-id>/02_selection.json

Stage E (LLM tiebreak) is NOT done here — we only set `stage_e_invoked: true`
when the score margin is small. The state-driver dispatches the
`triz-matrix-selector` subagent based on that flag.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import jsonschema

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402


# v0 weights (uncalibrated heuristics; design v6 §14.1 Stage D).
WEIGHTS_VERSION = "v0"
W1_DOMAIN_OVERLAP = 10
W2_CLASS_MATCH = 20
W4_EXOTIC_MATCH = 8
STATUS_WEIGHTS = {
    "canonical": 5,
    "domain": 15,        # boosted further if domain class matches; see _status_bonus
    "variant": -2,
    "derived": -3,
    "experimental": 0,
    "shell": 0,           # filtered at Stage A
    "identical-duplicate": 0,  # filtered at Stage A
}
SUPPORTED_LANGUAGES = ["en"]
STAGE_E_MARGIN = 0.15
MAX_REDIRECT_DEPTH = 3


# --- Stage helpers --------------------------------------------------------

def _matrix_supported_lang(reg_entry: dict) -> bool:
    langs = reg_entry.get("language") or []
    return any(l in SUPPORTED_LANGUAGES for l in langs)


def _matrix_loadable(reg_entry: dict) -> tuple[bool, str | None]:
    try:
        _common.load_matrix(reg_entry["id"])
    except Exception as e:
        return False, f"load failed: {type(e).__name__}: {e}"
    return True, None


def _domain_excludes_intersect(
    use_case: dict, problem_signals: list[str]
) -> set[str]:
    sel = (use_case.get("selector_tags") or {})
    excludes = set(sel.get("excludes") or [])
    return excludes & set(problem_signals)


# --- Stage C: redirect DSL evaluation -------------------------------------

def _eval_predicate(pred: dict, problem: dict) -> bool:
    """Single predicate per design v6 §14.2 / storage amendment 1."""
    if "exotic_signal" in pred:
        return pred["exotic_signal"] in (problem.get("exotic_signals") or [])
    if "domain_signal" in pred:
        return pred["domain_signal"] in (problem.get("domain_signals") or [])
    if "contradiction_type_is" in pred:
        return pred["contradiction_type_is"] == problem.get("contradiction_type")
    if "domain_class_is" in pred:
        return pred["domain_class_is"] == problem.get("domain_class")
    if "language_is" in pred:
        # Problem doesn't carry language; treat as English-only at v0.1.
        return pred["language_is"] in SUPPORTED_LANGUAGES
    if "populated_cells_at_least" in pred:
        # Predicate against the *target* matrix; not meaningful in problem
        # context. Always true here; redirect target is checked separately.
        return True
    raise ValueError(f"unknown predicate: {pred!r}")


def _eval_if(cond: dict, problem: dict) -> bool:
    if "any_of" in cond:
        return any(_eval_if(c, problem) for c in cond["any_of"])
    if "all_of" in cond:
        return all(_eval_if(c, problem) for c in cond["all_of"])
    if "not" in cond:
        return not _eval_if(cond["not"], problem)
    return _eval_predicate(cond, problem)


def _resolve_redirects(
    matrix_id: str,
    problem: dict,
    use_case_loader,
    excluded_ids: set[str],
    depth: int = 0,
    visited: set[str] | None = None,
    log: list[dict] | None = None,
) -> str:
    """Walk skip_in_favor_of with cycle detection. Returns final matrix id."""
    if visited is None:
        visited = set()
    if log is None:
        log = []
    if depth >= MAX_REDIRECT_DEPTH:
        return matrix_id
    visited = visited | {matrix_id}
    uc = use_case_loader(matrix_id)
    redirects = (
        (uc.get("when_to_use") or {}).get("skip_in_favor_of") or []
    )
    for entry in redirects:
        target = entry.get("target_matrix_id")
        if not target:
            continue
        if target in visited:
            log.append({"from": matrix_id, "to": target, "skipped": "cycle"})
            continue
        if target in excluded_ids:
            log.append({"from": matrix_id, "to": target, "skipped": "stage_a_excluded"})
            continue
        cond = entry.get("if")
        if cond is None:
            continue
        try:
            if _eval_if(cond, problem):
                log.append({"from": matrix_id, "to": target, "matched": True})
                return _resolve_redirects(
                    target, problem, use_case_loader, excluded_ids,
                    depth + 1, visited, log,
                )
        except ValueError as e:
            log.append({"from": matrix_id, "to": target, "error": str(e)})
            continue
    return matrix_id


# --- Stage D: scoring -----------------------------------------------------

def _status_bonus(reg_entry: dict, problem: dict) -> float:
    status = reg_entry.get("status", "")
    bonus = float(STATUS_WEIGHTS.get(status, 0))
    # The `domain` status gets an extra boost when the matrix's principle
    # taxonomy / domain matches the problem's domain class. The status weight
    # alone undersells domain matrices when they're the right tool.
    if status == "domain":
        # Heuristic: if the problem's domain_class appears in the use-case
        # selector_tags.domains, we count that as a domain match.
        try:
            uc = _common.load_use_case(reg_entry["id"])
            domains = set(((uc.get("selector_tags") or {}).get("domains") or []))
            if problem.get("domain_class") and problem["domain_class"] in domains:
                bonus += 0  # status_weights["domain"] is already 15; no extra
        except Exception:
            pass
    return bonus


def _score_matrix(reg_entry: dict, problem: dict) -> tuple[float, dict]:
    uc = _common.load_use_case(reg_entry["id"])
    sel = (uc.get("selector_tags") or {})
    domains = set(sel.get("domains") or [])
    classes = set(sel.get("problem_classes") or [])
    tags = set(sel.get("tags") or [])

    p_domain_signals = set(problem.get("domain_signals") or [])
    p_exotic = set(problem.get("exotic_signals") or [])
    p_class = problem.get("contradiction_type")

    domain_overlap = len(p_domain_signals & domains) * W1_DOMAIN_OVERLAP
    class_match = W2_CLASS_MATCH if (p_class in classes) else 0
    status_bonus = _status_bonus(reg_entry, problem)
    exotic_match = len(p_exotic & tags) * W4_EXOTIC_MATCH

    score = float(domain_overlap + class_match + status_bonus + exotic_match)
    breakdown = {
        "domain_overlap": domain_overlap,
        "class_match": class_match,
        "status_bonus": status_bonus,
        "exotic_match": exotic_match,
    }
    return score, breakdown


def _selection_confidence(score: float, top_score: float) -> str:
    if top_score <= 0:
        return "low"
    rel = score / top_score
    if rel >= 0.85:
        return "high"
    if rel >= 0.55:
        return "medium"
    return "low"


# --- Main pipeline --------------------------------------------------------

def select(
    problem: dict,
    matrix_overrides: list[str] | None = None,
) -> dict:
    """Run Stages A-D and produce a 02_selection.json-shaped dict.

    matrix_overrides: when the user passed --matrix=<id>, Stage A and B drops
    are bypassed for those ids (per design v6 §14.1 Stage A "no override").
    """
    overrides = set(matrix_overrides or [])
    framing_confidence = problem.get("framing_confidence", "medium")

    registry = _common.load_registry()
    candidates = registry.get("matrices", [])
    rejected: list[dict] = []

    # Stage A: hard exclude
    surviving: list[dict] = []
    for entry in candidates:
        mid = entry.get("id")
        if mid in overrides:
            surviving.append(entry)
            continue
        status = entry.get("status")
        pop = (entry.get("dimensions") or {}).get("populated_cells", 0)
        if status in {"identical-duplicate", "shell"}:
            rejected.append({"matrix_id": mid, "stage": "A",
                             "reason": f"status={status}"})
            continue
        if pop == 0:
            rejected.append({"matrix_id": mid, "stage": "A",
                             "reason": "populated_cells == 0"})
            continue
        if not _matrix_supported_lang(entry):
            rejected.append({"matrix_id": mid, "stage": "A",
                             "reason": f"language {entry.get('language')} "
                                       f"not in {SUPPORTED_LANGUAGES}"})
            continue
        try:
            uc = _common.load_use_case(mid)
        except Exception as e:
            rejected.append({"matrix_id": mid, "stage": "A",
                             "reason": f"use_case load failed: {e}"})
            continue
        intersect = _domain_excludes_intersect(
            uc, problem.get("domain_signals") or [],
        )
        if intersect:
            rejected.append({"matrix_id": mid, "stage": "A",
                             "reason": f"problem domain_signals intersect "
                                       f"matrix excludes: {sorted(intersect)}"})
            continue
        ok, err = _matrix_loadable(entry)
        if not ok:
            rejected.append({"matrix_id": mid, "stage": "A",
                             "reason": err or "load failed"})
            continue
        surviving.append(entry)

    # Stage B: status floor
    after_b: list[dict] = []
    for entry in surviving:
        mid = entry.get("id")
        if (entry.get("status") == "experimental"
                and framing_confidence == "high"
                and mid not in overrides):
            rejected.append({"matrix_id": mid, "stage": "B",
                             "reason": "experimental dropped at high framing_confidence"})
            continue
        after_b.append(entry)

    # Stage C: redirect resolution
    excluded_ids = {r["matrix_id"] for r in rejected}
    redirected: list[dict] = []
    redirect_logs: list[dict] = []
    seen_after_redirect: set[str] = set()
    for entry in after_b:
        mid = entry.get("id")
        log: list[dict] = []
        final_id = _resolve_redirects(
            mid, problem, _common.load_use_case, excluded_ids, log=log,
        )
        if log:
            redirect_logs.extend(log)
        if final_id != mid:
            try:
                final_entry = next(e for e in registry["matrices"]
                                   if e.get("id") == final_id)
            except StopIteration:
                # Target not in registry — keep original.
                redirected.append(entry)
                continue
            if final_id in seen_after_redirect:
                continue
            seen_after_redirect.add(final_id)
            redirected.append(final_entry)
            rejected.append({
                "matrix_id": mid, "stage": "C",
                "reason": f"redirected to {final_id}",
            })
        else:
            if mid not in seen_after_redirect:
                seen_after_redirect.add(mid)
                redirected.append(entry)

    # Stage D: scoring
    scored: list[tuple[dict, float, dict]] = []
    for entry in redirected:
        score, breakdown = _score_matrix(entry, problem)
        scored.append((entry, score, breakdown))
    scored.sort(key=lambda t: t[1], reverse=True)

    if not scored:
        # Stage A dropped everything. Caller (state-driver) will surface
        # ask_user; we emit an empty selection that fails schema (selected
        # has minItems: 1) on purpose so the contract violation is loud.
        return {
            "schema_version": 1,
            "weights_version": WEIGHTS_VERSION,
            "selected_matrices": [],
            "rejected_matrices": rejected,
            "run_strategy": "single",
            "stage_e_invoked": False,
            "redirect_log": redirect_logs,
        }

    top_score = scored[0][1]
    # Selection: keep only matrices with positive score (>0); always keep top 1.
    # Multi-matrix triangulation is enabled when ≥2 within stage_e margin AND
    # parameter_taxonomy values are distinct.
    selected_entries: list[tuple[dict, float, dict]] = [scored[0]]
    for entry, score, bk in scored[1:]:
        if score <= 0:
            continue
        margin = (top_score - score) / top_score if top_score > 0 else 1.0
        if margin <= STAGE_E_MARGIN:
            selected_entries.append((entry, score, bk))

    # run_strategy: parallel iff ≥2 selected AND parameter_taxonomy values are distinct
    taxonomies = {(e.get("parameter_id_style"), e.get("principle_taxonomy"))
                  for e, _, _ in selected_entries}
    if len(selected_entries) >= 2 and len(taxonomies) >= 2:
        run_strategy = "parallel"
    else:
        run_strategy = "single"
        # Demote to single matrix if not parallel.
        selected_entries = selected_entries[:1]

    # Stage E flag: if top vs second margin is < 15%, an LLM tiebreak might
    # help. We still return the deterministic selection; the state-driver
    # decides whether to dispatch the subagent based on this flag.
    stage_e_invoked = False
    if len(scored) >= 2 and top_score > 0:
        margin = (top_score - scored[1][1]) / top_score
        if margin < STAGE_E_MARGIN:
            stage_e_invoked = True

    selected = []
    for entry, score, bk in selected_entries:
        rationale_parts = [f"{k}={v:g}" for k, v in bk.items() if v]
        rationale = (
            f"selected by Stage D scoring: " + ", ".join(rationale_parts)
            if rationale_parts else "selected by Stage D scoring (no positive components)"
        )
        selected.append({
            "matrix_id": entry["id"],
            "score": score,
            "rationale": rationale,
            "selection_confidence": _selection_confidence(score, top_score),
            "score_breakdown": bk,
            "status": entry.get("status"),
            "parameter_id_style": entry.get("parameter_id_style"),
            "principle_taxonomy": entry.get("principle_taxonomy"),
            "interpretation_lineage": entry.get("interpretation_lineage"),
        })

    # Append losers (positive-score but cut by margin or strategy) to rejected.
    selected_ids = {s["matrix_id"] for s in selected}
    for entry, score, bk in scored:
        mid = entry["id"]
        if mid in selected_ids:
            continue
        if any(r["matrix_id"] == mid for r in rejected):
            continue
        rejected.append({
            "matrix_id": mid, "stage": "D",
            "reason": "lost on Stage D score margin",
            "score": score,
        })

    return {
        "schema_version": 1,
        "weights_version": WEIGHTS_VERSION,
        "selected_matrices": selected,
        "rejected_matrices": rejected,
        "run_strategy": run_strategy,
        "stage_e_invoked": stage_e_invoked,
        "redirect_log": redirect_logs,
    }


def _validate(selection: dict) -> None:
    schema = _common.load_schema("02_selection.schema.json")
    jsonschema.Draft202012Validator(schema).validate(selection)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="select_matrix.py",
        description="Run Stages A-D of matrix selection. Writes 02_selection.json.",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--matrix", action="append", default=None,
        help="Override: force-include this matrix id "
             "(may be passed multiple times). Bypasses Stage A and B drops.",
    )
    args = parser.parse_args(argv)

    try:
        problem = _common.read_artifact(args.run_id, "01_problem.json")
    except FileNotFoundError:
        print(
            f"select_matrix: 01_problem.json not found for run {args.run_id}. "
            f"Run the framer first.",
            file=sys.stderr,
        )
        return 2

    selection = select(problem, matrix_overrides=args.matrix)

    try:
        _validate(selection)
    except jsonschema.ValidationError as e:
        # Most likely cause: Stage A dropped everything (selected_matrices empty).
        print(
            f"select_matrix: produced selection failed schema validation: "
            f"{e.message}\n"
            f"  Path: {list(e.absolute_path)}\n"
            f"  Likely cause: no matrices survived Stage A. See "
            f"02_selection.json:rejected_matrices.",
            file=sys.stderr,
        )
        # Still write the artifact so the state-driver / user can inspect it.
        _common.write_artifact(args.run_id, "02_selection.json", selection)
        return 3

    out = _common.write_artifact(args.run_id, "02_selection.json", selection)
    print(f"select_matrix: wrote {out} "
          f"(selected={len(selection['selected_matrices'])}, "
          f"strategy={selection['run_strategy']}, "
          f"stage_e_invoked={selection['stage_e_invoked']})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"select_matrix: internal error: {type(e).__name__}: {e}",
              file=sys.stderr)
        sys.exit(2)
