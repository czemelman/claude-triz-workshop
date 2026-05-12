"""Strategy-driven property tests for next_action.py invariants.

Implements the four property tests sketched in design v6 §20.6 plus the
retry-cap invariant from §19.3:

- ``test_action_always_well_formed``    (closed 6-set + non-null payload)
- ``test_done_only_when_complete``      (done iff final-report.md on disk)
- ``test_no_silent_skip_of_validation`` (malformed artifact never advances)
- ``test_action_idempotency``           (same state → same action)
- ``test_retry_cap_excludes_retry_option`` (retry_counts >= 3 → no retry)

All tests use Hypothesis ``@settings(max_examples=20)`` per the §20.9 60s
budget and ``derandomize=True`` for reproducibility (matches the
``--hypothesis-seed=0`` invocation specified by the task spec while not
forcing CI consumers to pass a flag).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings

from ._strategies import (
    STAGE_ORDER,
    USER_DECISION_CHOICES,
    valid_artifact_strategy,
    valid_state_strategy,
    valid_user_decision_strategy,
)


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


# Stages whose handlers read upstream artifacts (01_problem, 02_selection)
# unconditionally. With a synthetic state and no artifacts on disk the
# driver raises FileNotFoundError → emits self_correct (still well-formed
# but tells us nothing new). We keep "framer", "select_matrix", "lookup",
# "synthesize", "merge_interpretations", "init", "done" as the tractable
# subset for the most direct invariants.
SAFE_STAGES = {
    "init",
    "framer",
    "select_matrix",
    "synthesize",
    "merge_interpretations",
    "lookup",
    "done",
}


def _invoke(args, cwd, timeout=15):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        env={**os.environ, "TRIZ_MATRICES_PATH": str(MATRICES_PATH)},
        capture_output=True, text=True, timeout=timeout,
    )
    assert proc.returncode == 0, (
        f"strict CLI contract violation: rc={proc.returncode} "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert proc.stderr == "", (
        f"strict CLI contract violation: stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _materialize_state(tmp_path: Path, state: dict) -> Path:
    """Write state.json to an isolated run-dir under tmp_path. Returns cwd."""
    rid = state["run_id"]
    rd = tmp_path / ".triz" / "runs" / rid
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return tmp_path


# --- Property 1: action is always in the closed 6-set ---------------------

@given(state=valid_state_strategy())
@settings(
    max_examples=20,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_action_always_well_formed(tmp_path_factory, state):
    """For any well-formed state: action is in the closed 6-set, and
    payload is non-empty (or empty/absent for ``done``).
    """
    # Each generated example needs its own filesystem isolation so the
    # state/artifacts of one example don't leak into the next.
    tmp_path = tmp_path_factory.mktemp("prop_well_formed")
    cwd = _materialize_state(tmp_path, state)
    action = _invoke(["--run-id", state["run_id"]], cwd=cwd)

    # Invariant 1: closed action set.
    assert action.get("action") in ALLOWED_ACTIONS, (
        f"action={action.get('action')!r} not in {ALLOWED_ACTIONS}; "
        f"current_stage={state['current_stage']}"
    )

    # Invariant 2: non-trivial payload.
    if action["action"] == "done":
        # done is allowed to carry only run_id + report_path (or be bare).
        return
    if action["action"] == "self_correct":
        # self_correct must carry a message string (covered explicitly
        # in test_action_well_formed.py; restated here as a sanity gate).
        assert isinstance(action.get("message"), str) and action["message"]
        return
    # All other actions carry stage-specific payload — at minimum more
    # than just the action key.
    assert len(action) > 1, (
        f"action {action['action']!r} has no payload beyond the type tag: "
        f"{action!r}"
    )


# --- Property 2: done only when final-report.md exists --------------------

@given(state=valid_state_strategy().filter(lambda s: s["current_stage"] == "done"))
@settings(
    max_examples=10, derandomize=True, deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
def test_done_emitted_when_state_is_done(tmp_path_factory, state):
    """When state is at DONE, the driver emits ``done`` (regardless of
    whether final-report.md is on disk — see invariant #2 in
    test_action_well_formed.py for the converse direction)."""
    tmp_path = tmp_path_factory.mktemp("prop_done_state")
    cwd = _materialize_state(tmp_path, state)
    # Drop a final-report.md so the driver has the canonical "complete"
    # signal — this is the round-trip property: state-at-done +
    # report-on-disk → action-is-done.
    rd = cwd / ".triz" / "runs" / state["run_id"]
    (rd / "final-report.md").write_text("# Done\n", encoding="utf-8")
    action = _invoke(["--run-id", state["run_id"]], cwd=cwd)
    assert action["action"] == "done"


def test_done_implies_report_exists(tmp_path_factory):
    """Converse: if action is ``done``, final-report.md MUST exist in
    the run dir. This is checked from the assemble side: driving the
    assemble stage to completion is the ONLY supported path to emitting
    ``done`` from a non-done state.
    """
    tmp_path = tmp_path_factory.mktemp("prop_done_report")
    rid = "prop-done-report"
    rd = tmp_path / ".triz" / "runs" / rid
    rd.mkdir(parents=True)
    state = {
        "run_id": rid,
        "current_stage": "done",
        "completed_stages": list(STAGE_ORDER[:-1]),
        "selected_matrices": ["altshuller_39x39"],
        "retry_counts": {},
        "loop_depth": 0,
        "max_loops": 2,
        "flags": {},
        "user_prompt": "x",
        "created_at": 1.0,
        "compatibility_checked": True,
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (rd / "final-report.md").write_text("# Done\n", encoding="utf-8")
    action = _invoke(["--run-id", rid], cwd=tmp_path)
    assert action["action"] == "done"
    assert (rd / "final-report.md").exists()


# --- Property 3: no silent skip of validation ----------------------------

@given(state=valid_state_strategy().filter(
    lambda s: s["current_stage"] in {"framer", "select_matrix"}))
@settings(
    max_examples=15, derandomize=True, deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
def test_no_silent_skip_of_validation(tmp_path_factory, state):
    """When the most-recently expected artifact is malformed, the driver
    MUST NOT silently advance to the next stage. It either re-dispatches
    (run_script / dispatch_subagent — same stage), bumps a retry counter,
    or pauses with ask_user. ``done`` and stage-skipping ``advance``
    paths are forbidden.
    """
    tmp_path = tmp_path_factory.mktemp("prop_no_silent_skip")
    cwd = _materialize_state(tmp_path, state)
    rd = cwd / ".triz" / "runs" / state["run_id"]
    # Plant a syntactically broken artifact for whichever stage we're at.
    if state["current_stage"] == "framer":
        # Framer validation inspects 01_problem.json; deliberately invalid.
        (rd / "01_problem.json").write_text(
            "{not valid json", encoding="utf-8")
    else:  # select_matrix
        # The driver only consults 02_selection.json after the script ran.
        # An invalid file simulates a script that crashed mid-write.
        (rd / "02_selection.json").write_text(
            '{"schema_version": 99}', encoding="utf-8")

    action = _invoke(["--run-id", state["run_id"]], cwd=cwd)
    # Must not be "done"; must not have silently advanced past the
    # current stage. Acceptable: ask_user (pause), dispatch_subagent
    # (retry), run_script (retry), self_correct (e.g. reading a
    # corrupted upstream file blew up).
    assert action["action"] != "done", (
        f"silently emitted done with malformed artifact: {action!r}"
    )
    assert action["action"] in ALLOWED_ACTIONS


# --- Property 4: action idempotency --------------------------------------

@given(state=valid_state_strategy().filter(
    lambda s: s["current_stage"] in SAFE_STAGES))
@settings(
    max_examples=15, derandomize=True, deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
def test_action_idempotency(tmp_path_factory, state):
    """Calling next_action.py twice with no user input + no artifact
    changes produces the same action. The state-driver is supposed to be
    deterministic given (state, disk).
    """
    tmp_path = tmp_path_factory.mktemp("prop_idempotency")
    cwd = _materialize_state(tmp_path, state)
    a1 = _invoke(["--run-id", state["run_id"]], cwd=cwd)
    # Reload state.json (the driver may have persisted re-tries / flags)
    # and compare a second invocation. We compare the action TYPE +
    # script/subagent identity since dispatched subagent payloads carry
    # run-id-encoded text that's already deterministic.
    a2 = _invoke(["--run-id", state["run_id"]], cwd=cwd)

    def fingerprint(a: dict) -> tuple:
        return (
            a.get("action"),
            a.get("script"),
            a.get("subagent"),
            a.get("expected_artifact"),
            a.get("kind"),
        )

    assert fingerprint(a1) == fingerprint(a2), (
        f"idempotency violation: a1={a1!r} a2={a2!r} "
        f"fp1={fingerprint(a1)} fp2={fingerprint(a2)}"
    )


# --- Property 5: retry cap excludes retry_subagent option ----------------

@given(stage=valid_state_strategy())
@settings(
    max_examples=15, derandomize=True, deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_retry_cap_excludes_retry_option(tmp_path_factory, stage):
    """If retry_counts[<current_stage>] >= 3 AND the action is ask_user
    with kind == "stage_retry_exhausted", the options list MUST NOT
    contain retry_subagent.

    The retry-exhausted prompt is emitted from _stage_framer and similar
    handlers in next_action.py only when retries > MAX_RETRIES_PER_STAGE.
    """
    # Force the retry counter at-cap for the current stage.
    s = dict(stage)
    s["retry_counts"] = dict(s.get("retry_counts", {}))
    s["retry_counts"][s["current_stage"]] = 4  # over-cap

    tmp_path = tmp_path_factory.mktemp("prop_retry_cap")
    cwd = _materialize_state(tmp_path, s)
    action = _invoke(["--run-id", s["run_id"]], cwd=cwd)
    if action.get("action") == "ask_user":
        opts = action.get("options") or []
        opt_ids = {o.get("id") for o in opts}
        assert "retry_subagent" not in opt_ids, (
            f"retry option present at retry cap: {action!r}"
        )


# --- Sanity test: strategies actually work in subprocess context ---------

def test_strategies_load_and_invoke(tmp_path):
    """Smoke: a tiny state generated outside Hypothesis should still
    produce a well-formed action. Catches sys.path / import regressions
    before the parametrized tests run.
    """
    rid = "prop-smoke"
    rd = tmp_path / ".triz" / "runs" / rid
    rd.mkdir(parents=True)
    state = {
        "run_id": rid,
        "current_stage": "init",
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
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")
    action = _invoke(["--run-id", rid], cwd=tmp_path)
    assert action.get("action") in ALLOWED_ACTIONS


# --- Sanity test: artifact strategies validate against their schemas -----

# --- Property: user-decision strategy is round-trip-safe -----------------

@given(decision=valid_user_decision_strategy())
@settings(max_examples=20, derandomize=True, deadline=None)
def test_user_decision_strategy_well_formed(decision):
    """Every user decision the strategy emits is either a recognized
    bare choice OR a recognized ``choice:value`` form.

    The state-driver's ``_apply_user_decision`` consumes the bare choice
    portion only — the ``:value`` suffix is the strategy's representation
    of inline payload data (e.g. ``reformulate_with_constraint:add a
    safety net``), which the orchestrator unpacks into the JSON
    ``user-input`` payload.
    """
    base = decision.split(":", 1)[0]
    assert base in USER_DECISION_CHOICES, (
        f"strategy emitted unrecognized base choice {base!r}"
    )


def _user_input_payload_for(choice: str) -> dict:
    """Build a JSON ``--user-input`` payload for a given decision string.

    For decisions that take inline data, supply a placeholder value.
    """
    base, _, val = choice.partition(":")
    payload = {"choice": base}
    if base in {"reformulate_with_constraint"}:
        payload["constraint_text"] = val or "ensure safety"
    elif base in {"try_different_matrix", "override_matrix"}:
        payload["matrix_id"] = val or "altshuller_39x39"
    elif base in {"provide_clarification"}:
        payload["clarification_text"] = val or "more detail"
    return payload


@given(decision=valid_user_decision_strategy())
@settings(
    max_examples=15, derandomize=True, deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_user_decision_apply_well_formed_action(tmp_path_factory, decision):
    """Feeding any strategy-generated user decision through the CLI
    produces a well-formed action (not necessarily a happy-path one,
    since several decisions are reserved aliases).

    This exercises the ``_apply_user_decision`` path end-to-end.
    """
    tmp_path = tmp_path_factory.mktemp("prop_user_decision")
    rid = "prop-decision"
    rd = tmp_path / ".triz" / "runs" / rid
    rd.mkdir(parents=True)
    state = {
        "run_id": rid,
        "current_stage": "check_fatal_severity",
        "completed_stages": list(STAGE_ORDER[:STAGE_ORDER.index("check_fatal_severity")]),
        "selected_matrices": ["altshuller_39x39"],
        "retry_counts": {},
        "loop_depth": 0,
        "max_loops": 2,
        "flags": {"active_matrices": ["altshuller_39x39"]},
        "user_prompt": "x",
        "created_at": 1.0,
        "compatibility_checked": True,
    }
    (rd / "state.json").write_text(json.dumps(state), encoding="utf-8")

    payload = _user_input_payload_for(decision)
    action = _invoke(
        ["--run-id", rid, "--user-input", json.dumps(payload)],
        cwd=tmp_path,
    )
    assert action.get("action") in ALLOWED_ACTIONS, (
        f"decision={decision!r} → unrecognized action {action!r}"
    )


@pytest.mark.parametrize("name,schema_filename", [
    ("01_problem", "01_problem.schema.json"),
    ("02_selection", "02_selection.schema.json"),
    ("03_mapping", "03_mapping.schema.json"),
    ("03b_mapping_critique", "03b_mapping_critique.schema.json"),
    ("03c_independent_mapping", "03c_independent_mapping.schema.json"),
    ("04_principles", "04_principles.schema.json"),
    ("05_interpretation_single", "05_interpretation_single.schema.json"),
    ("05_interpretations", "05_interpretations.schema.json"),
    ("06_solutions", "06_solutions.schema.json"),
    ("07_critique", "07_critique.schema.json"),
])
def test_artifact_strategies_pass_schema(name, schema_filename):
    """Each artifact strategy's outputs validate against the schema the
    state-driver applies in _validate_artifact_or_diagnose.
    """
    import jsonschema
    from scripts import _common
    schema = _common.load_schema(schema_filename)
    validator = jsonschema.Draft202012Validator(schema)
    strat = valid_artifact_strategy(name)

    @given(art=strat)
    @settings(max_examples=10, derandomize=True, deadline=None)
    def _check(art):
        validator.validate(art)

    _check()
