"""Unit tests for the severity bucketing in `_stage_check_fatal`.

The brief (B7) calls this categorize_severity. The actual implementation is
inline in `next_action._stage_check_fatal`:

    fatal = [c for c in crits if c.get("severity") == "fatal"]
    if not fatal:                   → none_fatal     (proceed to assemble)
    elif len(fatal) == len(crits):  → all_fatal      (ask_user, no drop_fatal_proceed option)
    else:                            → some_fatal     (ask_user, includes drop_fatal_proceed)

We test it in two ways:
1. Direct: import _stage_check_fatal and exercise it against synthetic state.
2. Integration-light: inspect the option set on the emitted ask_user.
"""

from __future__ import annotations

import enum
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import _common  # noqa: E402  (registered by conftest sys.path manipulation)
from scripts.next_action import _stage_check_fatal  # noqa: E402


class _Sev(enum.Enum):
    NONE = "none_fatal"
    SOME = "some_fatal"
    ALL = "all_fatal"


def _categorize(critiques: list[dict]) -> _Sev:
    fatal = [c for c in critiques if c.get("severity") == "fatal"]
    if not fatal:
        return _Sev.NONE
    if len(fatal) == len(critiques):
        return _Sev.ALL
    return _Sev.SOME


# --- Pure categorization logic (mirrors what _stage_check_fatal does) -----

def test_none_fatal_when_all_moderate():
    crits = [
        {"candidate_name": "A", "severity": "moderate"},
        {"candidate_name": "B", "severity": "minor"},
        {"candidate_name": "C", "severity": "severe"},
    ]
    assert _categorize(crits) == _Sev.NONE


def test_none_fatal_when_empty():
    # Defensive: an empty critique list (schema requires minItems=1, so this
    # cannot legitimately occur, but the bucketer must not crash).
    assert _categorize([]) == _Sev.NONE


def test_some_fatal_when_one_of_three():
    crits = [
        {"candidate_name": "A", "severity": "fatal"},
        {"candidate_name": "B", "severity": "moderate"},
        {"candidate_name": "C", "severity": "severe"},
    ]
    assert _categorize(crits) == _Sev.SOME


def test_some_fatal_when_two_of_three():
    crits = [
        {"candidate_name": "A", "severity": "fatal"},
        {"candidate_name": "B", "severity": "fatal"},
        {"candidate_name": "C", "severity": "moderate"},
    ]
    assert _categorize(crits) == _Sev.SOME


def test_all_fatal_when_single_fatal():
    crits = [{"candidate_name": "A", "severity": "fatal"}]
    assert _categorize(crits) == _Sev.ALL


def test_all_fatal_when_multiple_all_fatal():
    crits = [
        {"candidate_name": "A", "severity": "fatal"},
        {"candidate_name": "B", "severity": "fatal"},
    ]
    assert _categorize(crits) == _Sev.ALL


# --- End-to-end via _stage_check_fatal ------------------------------------

def _setup_run(tmp_path: Path, critique: dict) -> tuple[dict, Path]:
    """Build a minimal state.json + 07_critique.json under .triz/runs/<id>/.

    Returns (state, cwd). The state is at stage CHECK_FATAL_SEVERITY so
    _stage_check_fatal will fire on first dispatch.
    """
    run_id = "test-cat-" + tmp_path.name[-6:].replace(".", "")
    rd = tmp_path / ".triz" / "runs" / run_id
    rd.mkdir(parents=True)
    (rd / "07_critique.json").write_text(
        json.dumps(critique, indent=2), encoding="utf-8",
    )
    state = {
        "run_id": run_id,
        "current_stage": _common.Stage.CHECK_FATAL_SEVERITY.value,
        "completed_stages": ["critique"],
        "selected_matrices": [],
        "retry_counts": {},
        "loop_depth": 0,
        "max_loops": 2,
        "flags": {},
        "user_prompt": "irrelevant",
        "created_at": 1.0,
        "compatibility_checked": True,
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return state, tmp_path


def _run_check_fatal_in_subprocess(cwd: Path, run_id: str) -> dict:
    """Invoke next_action.py and return the parsed action."""
    proc = subprocess.run(
        [sys.executable,
         str(Path(__file__).resolve().parent.parent.parent
             / "scripts" / "next_action.py"),
         "--run-id", run_id],
        cwd=str(cwd),
        env={**os.environ,
             "TRIZ_MATRICES_PATH": str(Path(__file__).resolve()
                                       .parent.parent.parent.parent)},
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, f"stderr={proc.stderr!r}"
    assert proc.stderr == "", f"stderr={proc.stderr!r}"
    return json.loads(proc.stdout)


def test_check_fatal_none_fatal_runs_assemble(tmp_path):
    crit = {"schema_version": 1, "per_solution_critiques": [
        {"candidate_name": "A", "severity": "moderate",
         "secondary_contradictions": [], "risks": [], "recommendation": "ok"},
    ]}
    state, cwd = _setup_run(tmp_path, crit)
    action = _run_check_fatal_in_subprocess(cwd, state["run_id"])
    # No fatal → proceed to assemble. The driver advances stage and emits
    # the assemble run_script action because final-report.md isn't there yet.
    assert action["action"] == "run_script"
    assert action["script"] == "assemble_report.py"
    assert "--no_resolution" not in action["args"]


def test_check_fatal_some_fatal_offers_drop_fatal_proceed(tmp_path):
    crit = {"schema_version": 1, "per_solution_critiques": [
        {"candidate_name": "A", "severity": "fatal",
         "secondary_contradictions": [], "risks": [], "recommendation": "no"},
        {"candidate_name": "B", "severity": "moderate",
         "secondary_contradictions": [], "risks": [], "recommendation": "ok"},
    ]}
    state, cwd = _setup_run(tmp_path, crit)
    action = _run_check_fatal_in_subprocess(cwd, state["run_id"])
    assert action["action"] == "ask_user"
    assert action["kind"] == "fatal_severity_in_critique"
    option_ids = {o["id"] for o in action["options"]}
    assert "drop_fatal_proceed" in option_ids
    assert "abandon_with_writeup" in option_ids


def test_check_fatal_all_fatal_omits_drop_fatal_proceed(tmp_path):
    crit = {"schema_version": 1, "per_solution_critiques": [
        {"candidate_name": "A", "severity": "fatal",
         "secondary_contradictions": [], "risks": [], "recommendation": "no"},
        {"candidate_name": "B", "severity": "fatal",
         "secondary_contradictions": [], "risks": [], "recommendation": "no"},
    ]}
    state, cwd = _setup_run(tmp_path, crit)
    action = _run_check_fatal_in_subprocess(cwd, state["run_id"])
    assert action["action"] == "ask_user"
    assert action["kind"] == "fatal_severity_in_critique"
    option_ids = {o["id"] for o in action["options"]}
    # drop_fatal_proceed must NOT appear when every candidate is fatal.
    assert "drop_fatal_proceed" not in option_ids
    # abandon_with_writeup is still available per design v6 §17.3.
    assert "abandon_with_writeup" in option_ids
