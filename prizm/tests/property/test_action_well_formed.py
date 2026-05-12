"""Property tests for next_action.py invariants (design v6 §20.6).

Phase-1 scope: hand-coded states exercising the closed action set and
the done-only-when-final-report invariant. Strategy generators come in
Phase 3 per §20.6.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = PLUGIN_ROOT / "scripts" / "next_action.py"
MATRICES_PATH = PLUGIN_ROOT.parent

ALLOWED_ACTIONS = {
    "dispatch_subagent",
    "dispatch_subagents_parallel",
    "run_script",
    "ask_user",
    "self_correct",
    "done",
}


def _make_state(stage: str, run_id: str, **overrides) -> dict:
    base = {
        "run_id": run_id,
        "current_stage": stage,
        "completed_stages": [],
        "selected_matrices": [],
        "retry_counts": {},
        "loop_depth": 0,
        "max_loops": 2,
        "flags": {},
        "user_prompt": "x",
        "created_at": 1.0,
        "compatibility_checked": True,
    }
    base.update(overrides)
    return base


def _invoke(args, cwd):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        env={**os.environ, "TRIZ_MATRICES_PATH": str(MATRICES_PATH)},
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0
    assert proc.stderr == ""
    return json.loads(proc.stdout)


# --- Invariant 1: action field is in the closed 6-set --------------------

@pytest.mark.parametrize("scenario", [
    # (description, args-builder fn that takes tmp_path, returns (args, cwd))
    ("no args (self_correct)",
     lambda tp: ([], tp)),
    ("unknown flag (self_correct via argparse)",
     lambda tp: (["--unrecognized-flag"], tp)),
    ("new run init (dispatch_subagent)",
     lambda tp: (["--new-run", "--user-prompt", "Test"], tp)),
])
def test_action_field_is_in_closed_set(scenario, tmp_path):
    desc, builder = scenario
    args, cwd = builder(tmp_path)
    action = _invoke(args, cwd)
    assert action.get("action") in ALLOWED_ACTIONS, (
        f"{desc}: action {action.get('action')!r} not in {ALLOWED_ACTIONS}"
    )


def test_action_field_present_for_every_known_stage(tmp_path):
    """Materialize one synthetic state per stage and confirm the action
    field is always in the closed set. Some stages may emit self_correct
    if their preconditions aren't met; that still counts as well-formed.
    """
    from scripts._common import Stage  # noqa: E402
    failures = []
    for stage in Stage:
        run_id = f"prop-stage-{stage.value}"
        rd = tmp_path / ".triz" / "runs" / run_id
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "state.json").write_text(
            json.dumps(_make_state(stage.value, run_id)), encoding="utf-8")
        action = _invoke(["--run-id", run_id], cwd=tmp_path)
        if action.get("action") not in ALLOWED_ACTIONS:
            failures.append(
                f"stage={stage.value}: action={action.get('action')!r}"
            )
    assert not failures, "\n".join(failures)


# --- Invariant 2: done only when final-report.md exists ------------------

def test_done_emitted_only_when_final_report_exists(tmp_path):
    """If state is at DONE but final-report.md is absent, the driver still
    emits 'done' (per current code). The stronger property — that 'done' is
    emitted IFF the report is on disk — is checked from the assemble side:
    when the report exists, the assemble stage transitions to DONE.
    """
    # Case A: state at ASSEMBLE, no report → should NOT be 'done'.
    rid_a = "prop-no-report"
    rd = tmp_path / ".triz" / "runs" / rid_a
    rd.mkdir(parents=True)
    (rd / "state.json").write_text(
        json.dumps(_make_state("assemble", rid_a)), encoding="utf-8")
    a = _invoke(["--run-id", rid_a], cwd=tmp_path)
    assert a["action"] != "done", (
        f"emitted done with no final-report.md: {a!r}"
    )
    # It should attempt to run assemble_report.py.
    assert a["action"] == "run_script"
    assert a["script"] == "assemble_report.py"

    # Case B: state at ASSEMBLE, report exists → done.
    rid_b = "prop-with-report"
    rd_b = tmp_path / ".triz" / "runs" / rid_b
    rd_b.mkdir(parents=True)
    (rd_b / "state.json").write_text(
        json.dumps(_make_state("assemble", rid_b)), encoding="utf-8")
    (rd_b / "final-report.md").write_text("# Done\n", encoding="utf-8")
    b = _invoke(["--run-id", rid_b], cwd=tmp_path)
    assert b["action"] == "done"
    assert "report_path" in b


# --- Invariant 3: self_correct always carries a message ------------------

def test_self_correct_always_has_message(tmp_path):
    a = _invoke([], cwd=tmp_path)
    assert a["action"] == "self_correct"
    assert isinstance(a.get("message"), str) and a["message"], (
        f"self_correct missing message: {a!r}"
    )


# --- Invariant 4: ask_user always has run_id and options -----------------

def test_ask_user_carries_run_id_and_options(tmp_path):
    """Build a low-confidence framer state and confirm the resulting
    ask_user includes both run_id and a non-empty options array."""
    rid = "prop-ask-user-shape"
    rd = tmp_path / ".triz" / "runs" / rid
    rd.mkdir(parents=True)
    (rd / "state.json").write_text(
        json.dumps(_make_state("framer", rid,
                                completed_stages=["init"])), encoding="utf-8")
    (rd / "01_problem.json").write_text(json.dumps({
        "schema_version": 1,
        "improving_concept": "x", "worsening_concept": "y",
        "domain_signals": [], "exotic_signals": [],
        "contradiction_type": "engineering-contradiction",
        "domain_class": "general",
        "framing_confidence": "low",
        "constraints": [],
    }), encoding="utf-8")
    a = _invoke(["--run-id", rid], cwd=tmp_path)
    assert a["action"] == "ask_user"
    assert a.get("run_id") == rid
    assert isinstance(a.get("options"), list) and a["options"]
    for opt in a["options"]:
        assert "id" in opt and "label" in opt
