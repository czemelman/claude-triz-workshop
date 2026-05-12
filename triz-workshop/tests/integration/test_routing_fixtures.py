"""Parameterized routing-fixture runner per design v6 §20.4.

For each `tests/fixtures/states/<NN>_<name>/` directory:

1. Materialize `state/` files into `tmp_path/.triz/runs/<run_id>/`.
2. Invoke `next_action.py` with the fixture's `invocation.json:args`.
3. Assert the strict CLI contract (exit=0, stderr empty, stdout valid JSON).
4. Compare the parsed action against `expected.json`.

Comparison strategy: assert `action` field always matches; for the deeper
fields, compare structural facts that are stable across runs (subagent id,
script name, action type, ask_user kind, option ids) rather than the full
prompt text — prompts contain the run_id, which differs between fixture
materialization and idealized expectation only when the fixture is `<new>`
(init).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from conftest import (  # noqa: E402
    FIXTURES_DIR,
    install_fixture,
    subprocess_run_next_action,
)


STATES_DIR = FIXTURES_DIR / "states"


def _fixture_dirs():
    if not STATES_DIR.exists():
        return []
    return sorted([p for p in STATES_DIR.iterdir() if p.is_dir()])


@pytest.mark.parametrize("fixture_dir", _fixture_dirs(),
                         ids=lambda p: p.name)
def test_state_fixture_routes_correctly(fixture_dir: Path, tmp_path: Path):
    """Run the fixture against next_action.py and verify the emitted action."""
    cwd, run_id, invocation = install_fixture(fixture_dir, tmp_path)
    expected = json.loads(
        (fixture_dir / "expected.json").read_text(encoding="utf-8")
    )
    args = list(invocation["args"])
    action = subprocess_run_next_action(*args, cwd=cwd)

    # Always compare the action field.
    assert action["action"] == expected["action"], (
        f"action mismatch in {fixture_dir.name}: "
        f"got {action['action']!r}, expected {expected['action']!r}\n"
        f"full action: {action!r}"
    )

    # Per-action-type structural assertions.
    if expected["action"] == "dispatch_subagent":
        assert action.get("subagent") == expected.get("subagent")
        assert action.get("expected_artifact") == expected.get("expected_artifact")

    elif expected["action"] == "run_script":
        assert action.get("script") == expected.get("script")
        assert action.get("expected_artifact") == expected.get("expected_artifact")
        # Compare args verbatim — they encode the routing decision (--matrix,
        # --no_resolution, --exclude, etc.).
        assert action.get("args") == expected.get("args"), (
            f"script args mismatch: got {action.get('args')!r}, "
            f"expected {expected.get('args')!r}"
        )

    elif expected["action"] == "dispatch_subagents_parallel":
        # Compare the SET of (subagent, expected_artifact) pairs — order may
        # differ between iterations but the set of dispatches is the routing
        # contract.
        got = sorted([(d.get("subagent"), d.get("expected_artifact"))
                      for d in action.get("dispatches", [])])
        exp = sorted([(d.get("subagent"), d.get("expected_artifact"))
                      for d in expected.get("dispatches", [])])
        assert got == exp, f"dispatches set mismatch: got {got!r}, expected {exp!r}"
        if "batch_size" in expected:
            assert action.get("batch_size") == expected["batch_size"]

    elif expected["action"] == "ask_user":
        assert action.get("kind") == expected.get("kind")
        # Compare the SET of option ids; the order is design-driven but
        # stable within a single state, so identity here is fine.
        got_opts = sorted(o["id"] for o in action.get("options", []))
        exp_opts = sorted(o["id"] for o in expected.get("options", []))
        assert got_opts == exp_opts, (
            f"ask_user options mismatch: got {got_opts!r}, expected {exp_opts!r}"
        )

    elif expected["action"] == "self_correct":
        # Self-correct messages are diagnostic; we just assert the action
        # shape and presence of message + hint.
        assert "message" in action

    elif expected["action"] == "done":
        # Both should mark completion.
        assert action["action"] == "done"
        # report_path may differ in absolute prefix between fixture and run;
        # we just check it's present.
        assert "report_path" in action
