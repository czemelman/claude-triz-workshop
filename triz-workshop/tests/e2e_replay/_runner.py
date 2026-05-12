"""Replay-runner helpers for the E2E replay smoke test (design v6 §20.7).

The runner walks the state-driver forward in a deterministic synthetic
run by:

1. Invoking ``next_action.py`` with the current run-id.
2. Recording the emitted action's fingerprint to ``trace_actions.jsonl``
   (one JSON line per consult, exactly as §20.7 prescribes).
3. Planting a stub artifact whose schema is satisfied so the *next*
   invocation advances the state machine. The stub planting is keyed off
   the action's ``expected_artifact`` field — no LLM is involved.

Stub artifacts are minimal (matrix_id + the schema's required fields).
This isn't a behavioral test of subagent quality; it's a regression
baseline for the action sequence the state-driver produces given a
canonical happy-path corpus.

The same module is used both to RECORD a trace (write the jsonl) and to
REPLAY a trace (compare against a saved jsonl). The §20.7 vision is
"anonymized real runs accumulate as long-form regression tests" — this
runner is the seed infrastructure for that.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = PLUGIN_ROOT / "scripts" / "next_action.py"
MATRICES_PATH = PLUGIN_ROOT.parent


# --- Action fingerprint ---------------------------------------------------

@dataclass(frozen=True)
class ActionFingerprint:
    """The stable shape of an action — strips the parts that change
    between runs (run_id-encoded prompts, free-form messages).

    The fingerprint is what we record in trace_actions.jsonl and what we
    compare across runs. Two actions with the same fingerprint are the
    "same" action for replay-equivalence purposes.
    """
    action: str
    script: str | None = None
    subagent: str | None = None
    kind: str | None = None
    expected_artifact: str | None = None
    expected_artifacts: tuple[str, ...] | None = None
    dispatches: tuple[tuple[str, str], ...] | None = None  # (subagent, artifact)

    @classmethod
    def of(cls, action: dict) -> "ActionFingerprint":
        kind = action.get("action")
        expected_artifacts = None
        dispatches = None
        if kind == "dispatch_subagents_parallel":
            ds = tuple(
                (d.get("subagent", ""), d.get("expected_artifact", ""))
                for d in action.get("dispatches", [])
            )
            dispatches = ds
            expected_artifacts = tuple(a for _, a in ds if a)
        return cls(
            action=kind,
            script=action.get("script"),
            subagent=action.get("subagent"),
            kind=action.get("kind"),
            expected_artifact=action.get("expected_artifact"),
            expected_artifacts=expected_artifacts,
            dispatches=dispatches,
        )

    def to_jsonable(self) -> dict[str, Any]:
        d = asdict(self)
        # Tuples are JSON-serializable as arrays; dataclasses.asdict
        # leaves them as-is, but JSON encoder coerces. Force lists for
        # stable on-disk shape.
        if d["expected_artifacts"] is not None:
            d["expected_artifacts"] = list(d["expected_artifacts"])
        if d["dispatches"] is not None:
            d["dispatches"] = [list(t) for t in d["dispatches"]]
        return d


# --- Stub artifact planters ----------------------------------------------

def _stub_for_artifact(artifact_name: str) -> dict | None:
    """Return a minimal valid JSON dict for the given artifact filename,
    or None if no stub is appropriate (e.g. the orchestrator runs a
    deterministic script that produces it on its own).
    """
    name = Path(artifact_name).name
    if name == "01_problem.json":
        return {
            "schema_version": 1,
            "improving_concept": "weight",
            "worsening_concept": "thermal performance",
            "domain_signals": ["mechanical"],
            "exotic_signals": [],
            "contradiction_type": "engineering-contradiction",
            "domain_class": "mechanical",
            "framing_confidence": "high",
            "constraints": [],
        }
    if name == "02_selection.json":
        return {
            "schema_version": 1,
            "weights_version": "v0",
            "selected_matrices": [{
                "matrix_id": "altshuller_39x39",
                "score": 50.0,
                "rationale": "selected: altshuller_39x39",
                "selection_confidence": "high",
            }],
            "rejected_matrices": [],
            "run_strategy": "single",
            "stage_e_invoked": False,
        }
    if name.startswith("03_mapping_"):
        mid = name[len("03_mapping_"):-len(".json")]
        return {
            "schema_version": 1,
            "matrix_id": mid,
            "improving_param_id": "1",
            "worsening_param_id": "9",
            "improving_rationale": "weight is the improving axis",
            "worsening_rationale": "thermal capacity is the worsening axis",
            "alternatives": [],
            "mapping_confidence": "high",
            "no_clean_mapping": False,
        }
    if name.startswith("03c_independent_mapping_"):
        mid = name[len("03c_independent_mapping_"):-len(".json")]
        return {
            "schema_version": 1,
            "matrix_id": mid,
            "improving_param_id": "1",
            "worsening_param_id": "9",
            "rationale": "independent mapping by critic",
            "confidence": "high",
            "no_clean_mapping": False,
        }
    if name.startswith("04_principles_"):
        mid = name[len("04_principles_"):-len(".json")]
        return {
            "schema_version": 1,
            "matrix_id": mid,
            "populated": True,
            "principles": [1, 8, 15, 29, 35, 40],
            "alternatives_tried": [],
        }
    return None


def plant_stub_for(action: dict, run_dir: Path) -> list[Path]:
    """Inspect the action; write stub artifacts for whatever it dispatched.

    Returns the list of files written so the caller can log/verify them.
    """
    written: list[Path] = []
    expected = action.get("expected_artifact")
    if expected:
        stub = _stub_for_artifact(expected)
        if stub is not None:
            (run_dir / expected).write_text(
                json.dumps(stub, indent=2), encoding="utf-8")
            written.append(run_dir / expected)
    for d in action.get("dispatches") or []:
        ea = d.get("expected_artifact")
        if not ea:
            continue
        stub = _stub_for_artifact(ea)
        if stub is not None:
            (run_dir / ea).write_text(
                json.dumps(stub, indent=2), encoding="utf-8")
            written.append(run_dir / ea)
    return written


# --- Driver invocation ---------------------------------------------------

def invoke_next_action(run_id: str, cwd: Path,
                       extra_args: list[str] | None = None,
                       timeout: float = 15.0) -> dict:
    """Run next_action.py and assert the strict CLI contract."""
    extra = list(extra_args or [])
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--run-id", run_id, *extra],
        cwd=str(cwd),
        env={**os.environ, "TRIZ_MATRICES_PATH": str(MATRICES_PATH)},
        capture_output=True, text=True, timeout=timeout,
    )
    assert proc.returncode == 0, (
        f"contract: rc must be 0; got {proc.returncode}, stderr={proc.stderr!r}"
    )
    assert proc.stderr == "", f"contract: stderr must be empty; got {proc.stderr!r}"
    return json.loads(proc.stdout)


# --- Bootstrap: a synthetic run primed at the FRAMER stage ---------------

def seed_run(cwd: Path, run_id: str, user_prompt: str) -> Path:
    """Create .triz/runs/<run_id>/state.json so the next invocation
    starts the framer dispatch. Returns the run directory."""
    rd = cwd / ".triz" / "runs" / run_id
    rd.mkdir(parents=True, exist_ok=True)
    state = {
        "run_id": run_id,
        "current_stage": "framer",
        "completed_stages": ["init"],
        "selected_matrices": [],
        "retry_counts": {},
        "loop_depth": 0,
        "max_loops": 2,
        "flags": {},
        "user_prompt": user_prompt,
        "created_at": 1.0,
        "compatibility_checked": True,
    }
    (rd / "state.json").write_text(json.dumps(state, indent=2),
                                   encoding="utf-8")
    return rd


# --- Run + record ---------------------------------------------------------

def run_and_record(cwd: Path, run_id: str, num_steps: int,
                   trace_path: Path | None = None,
                   ) -> list[ActionFingerprint]:
    """Drive ``num_steps`` consults of next_action.py, planting stub
    artifacts after each, and return the sequence of fingerprints.

    If ``trace_path`` is provided, also write each fingerprint as a JSON
    line to that file (the §20.7 jsonl format).
    """
    rd = cwd / ".triz" / "runs" / run_id
    fingerprints: list[ActionFingerprint] = []
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        # Open in write mode to start fresh each call.
        trace_path.write_text("", encoding="utf-8")
    for _ in range(num_steps):
        action = invoke_next_action(run_id, cwd)
        fp = ActionFingerprint.of(action)
        fingerprints.append(fp)
        if trace_path is not None:
            with open(trace_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(fp.to_jsonable()) + "\n")
        plant_stub_for(action, rd)
    return fingerprints


def load_trace(trace_path: Path) -> list[ActionFingerprint]:
    """Parse a jsonl trace into ActionFingerprint objects."""
    out: list[ActionFingerprint] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        ea = d.get("expected_artifacts")
        if ea is not None:
            d["expected_artifacts"] = tuple(ea)
        ds = d.get("dispatches")
        if ds is not None:
            d["dispatches"] = tuple(tuple(x) for x in ds)
        out.append(ActionFingerprint(**d))
    return out
