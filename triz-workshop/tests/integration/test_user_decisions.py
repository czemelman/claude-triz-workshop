"""Parameterized decision-fixture runner.

Same shape as `test_routing_fixtures.py` but iterates over
`tests/fixtures/decisions/`. Each invocation passes `--user-input` from
the fixture's `invocation.json:args` (which already encodes it).
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


DECISIONS_DIR = FIXTURES_DIR / "decisions"


def _fixture_dirs():
    if not DECISIONS_DIR.exists():
        return []
    return sorted([p for p in DECISIONS_DIR.iterdir() if p.is_dir()])


@pytest.mark.parametrize("fixture_dir", _fixture_dirs(),
                         ids=lambda p: p.name)
def test_decision_fixture_routes_correctly(fixture_dir: Path, tmp_path: Path):
    cwd, run_id, invocation = install_fixture(fixture_dir, tmp_path)
    expected = json.loads(
        (fixture_dir / "expected.json").read_text(encoding="utf-8")
    )
    args = list(invocation["args"])
    action = subprocess_run_next_action(*args, cwd=cwd)

    assert action["action"] == expected["action"], (
        f"action mismatch in {fixture_dir.name}: "
        f"got {action['action']!r}, expected {expected['action']!r}\n"
        f"full action: {action!r}"
    )

    if expected["action"] == "dispatch_subagent":
        assert action.get("subagent") == expected.get("subagent")
        assert action.get("expected_artifact") == expected.get("expected_artifact")

    elif expected["action"] == "run_script":
        assert action.get("script") == expected.get("script")
        assert action.get("expected_artifact") == expected.get("expected_artifact")
        assert action.get("args") == expected.get("args"), (
            f"script args mismatch: got {action.get('args')!r}, "
            f"expected {expected.get('args')!r}"
        )

    elif expected["action"] == "dispatch_subagents_parallel":
        got = sorted([(d.get("subagent"), d.get("expected_artifact"))
                      for d in action.get("dispatches", [])])
        exp = sorted([(d.get("subagent"), d.get("expected_artifact"))
                      for d in expected.get("dispatches", [])])
        assert got == exp

    elif expected["action"] == "ask_user":
        assert action.get("kind") == expected.get("kind")
        got_opts = sorted(o["id"] for o in action.get("options", []))
        exp_opts = sorted(o["id"] for o in expected.get("options", []))
        assert got_opts == exp_opts

    elif expected["action"] == "self_correct":
        assert "message" in action

    elif expected["action"] == "done":
        assert "report_path" in action
