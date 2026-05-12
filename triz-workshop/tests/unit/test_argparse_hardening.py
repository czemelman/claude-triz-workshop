"""Argparse hardening tests for next_action.py (design v6 §19.1).

The contract: argparse errors MUST NOT exit(2). They must always emit a
self_correct action on stdout, exit code 0, stderr empty.
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
MATRICES_PATH = PLUGIN_ROOT.parent  # for compatibility_check during init paths.


def _invoke(*args: str, cwd: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        env={**os.environ, "TRIZ_MATRICES_PATH": str(MATRICES_PATH)},
        capture_output=True, text=True, timeout=10,
    )
    # Strict CLI contract: always exit 0, stderr empty.
    assert proc.returncode == 0, (
        f"non-zero exit {proc.returncode}; stderr={proc.stderr!r}; "
        f"stdout={proc.stdout!r}"
    )
    assert proc.stderr == "", f"stderr should be empty: {proc.stderr!r}"
    return json.loads(proc.stdout.strip())


def test_unknown_flag_emits_self_correct(tmp_path):
    action = _invoke("--bogus-arg", cwd=tmp_path)
    assert action["action"] == "self_correct"
    assert "argparse" in action["message"].lower() or "unrecognized" in action["message"].lower()
    assert "hint" in action


def test_no_args_at_all_emits_self_correct(tmp_path):
    action = _invoke(cwd=tmp_path)
    assert action["action"] == "self_correct"
    assert "run-id" in action["message"].lower() or "new-run" in action["message"].lower()


def test_run_id_with_no_state_emits_self_correct(tmp_path):
    """Existing run-id but no state.json on disk."""
    action = _invoke("--run-id", "nonexistent-run", cwd=tmp_path)
    assert action["action"] == "self_correct"
    assert "state" in action["message"].lower() or "no state" in action["message"].lower()


def test_malformed_user_input_json_emits_self_correct(tmp_path):
    """A run with valid state but malformed --user-input must self_correct."""
    # Build a minimal valid state.
    run_id = "test-arg-malformed"
    rd = tmp_path / ".triz" / "runs" / run_id
    rd.mkdir(parents=True)
    state = {
        "run_id": run_id, "current_stage": "framer",
        "completed_stages": ["init"], "selected_matrices": [],
        "retry_counts": {}, "loop_depth": 0, "max_loops": 2,
        "flags": {}, "user_prompt": "x",
        "created_at": 1.0, "compatibility_checked": True,
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    action = _invoke(
        "--run-id", run_id, "--user-input", "not valid json",
        cwd=tmp_path,
    )
    assert action["action"] == "self_correct"
    assert "json" in action["message"].lower() or "user input" in action["message"].lower()


def test_user_input_missing_choice_field_emits_self_correct(tmp_path):
    run_id = "test-arg-no-choice"
    rd = tmp_path / ".triz" / "runs" / run_id
    rd.mkdir(parents=True)
    state = {
        "run_id": run_id, "current_stage": "framer",
        "completed_stages": ["init"], "selected_matrices": [],
        "retry_counts": {}, "loop_depth": 0, "max_loops": 2,
        "flags": {}, "user_prompt": "x",
        "created_at": 1.0, "compatibility_checked": True,
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    action = _invoke(
        "--run-id", run_id, "--user-input", '{"foo": "bar"}',
        cwd=tmp_path,
    )
    assert action["action"] == "self_correct"
    assert "choice" in action["message"].lower()


def test_unknown_choice_emits_self_correct(tmp_path):
    run_id = "test-arg-unknown-choice"
    rd = tmp_path / ".triz" / "runs" / run_id
    rd.mkdir(parents=True)
    state = {
        "run_id": run_id, "current_stage": "framer",
        "completed_stages": ["init"], "selected_matrices": [],
        "retry_counts": {}, "loop_depth": 0, "max_loops": 2,
        "flags": {}, "user_prompt": "x",
        "created_at": 1.0, "compatibility_checked": True,
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    action = _invoke(
        "--run-id", run_id, "--user-input", '{"choice": "totally_made_up"}',
        cwd=tmp_path,
    )
    assert action["action"] == "self_correct"
    assert "choice" in action["message"].lower()
