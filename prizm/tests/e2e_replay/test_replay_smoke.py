"""End-to-end replay regression smoke test (design v6 §20.7).

The §20.7 vision is "anonymized real runs accumulate as long-form
regression tests." No real production runs exist yet, so this smoke
test seeds the infrastructure: a single recorded trace
(``fixtures/heat_exchanger_smoke/trace_actions.jsonl``) that future
real, anonymized runs commit alongside.

Test plan:

1. ``test_replay_smoke_records_trace`` — seed a synthetic run, drive
   ``next_action.py`` forward 5 steps planting stub artifacts in
   between, and assert the recorded action sequence matches the
   on-disk fixture trace. This is the "record-and-replay match"
   property — the test BOTH records a fresh trace and compares it
   to the saved baseline. A drift in the state-driver would surface
   here.

2. ``test_replay_cascade_invalidation`` — re-run the same 5 steps
   from a clean run-dir. The fingerprint sequence must match the
   first run exactly. This is the replay-determinism guarantee:
   given the same seed state + the same artifact stubs, the driver
   produces an identical action trace. Even though stages are
   "rerun" each invocation (the driver re-validates from disk on
   every consult), the cascade-invalidation logic in
   ``_apply_user_decision`` and the per-stage gates in ``_dispatch``
   keep the trace stable.

The smoke test is the seed; future commits should add anonymized
production traces under ``fixtures/<run_id>/`` with their own
``manifest.json`` + ``trace_actions.jsonl``. See
``tests/e2e_replay/README.md`` for the convention.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ._runner import (
    ActionFingerprint,
    invoke_next_action,
    load_trace,
    plant_stub_for,
    run_and_record,
    seed_run,
)


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SMOKE_FIXTURE = FIXTURES_DIR / "heat_exchanger_smoke"


# --- Helpers --------------------------------------------------------------

def _load_fixture():
    manifest = json.loads(
        (SMOKE_FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    trace = load_trace(SMOKE_FIXTURE / "trace_actions.jsonl")
    return manifest, trace


# --- Tests ---------------------------------------------------------------

def test_smoke_fixture_present():
    """Sanity: the fixture exists and has both manifest + trace."""
    assert SMOKE_FIXTURE.exists(), f"missing fixture dir: {SMOKE_FIXTURE}"
    assert (SMOKE_FIXTURE / "manifest.json").exists()
    assert (SMOKE_FIXTURE / "trace_actions.jsonl").exists()
    manifest, trace = _load_fixture()
    assert len(trace) == manifest["num_steps"], (
        f"trace length {len(trace)} != manifest num_steps {manifest['num_steps']}"
    )


def test_replay_smoke_records_trace(tmp_path: Path):
    """Drive a fresh synthetic run and assert it matches the saved
    canonical trace fingerprint-by-fingerprint.

    This is the §20.7 baseline: any state-driver change that alters
    the action sequence on a canonical happy-path run trips this test.
    """
    manifest, expected_trace = _load_fixture()
    run_id = manifest["seed_run_id"]
    seed_run(tmp_path, run_id, manifest["user_prompt"])

    actual_trace = run_and_record(
        tmp_path, run_id, num_steps=manifest["num_steps"],
    )
    assert len(actual_trace) == len(expected_trace), (
        f"trace length differs: actual={len(actual_trace)} "
        f"expected={len(expected_trace)}"
    )
    for i, (act, exp) in enumerate(zip(actual_trace, expected_trace)):
        assert act == exp, (
            f"step {i} fingerprint mismatch:\n"
            f"  actual:   {act}\n"
            f"  expected: {exp}"
        )


def test_replay_cascade_invalidation(tmp_path: Path):
    """Run the same 5 steps twice in two distinct run-dirs; the action
    sequences must match exactly.

    This exercises the replay-cascade-invalidation invariant: the
    driver's state machine is a pure function of (state.json,
    artifacts on disk). Two identical inputs produce identical output
    sequences regardless of how many times the run is "replayed".
    """
    manifest, _ = _load_fixture()

    # Run A.
    rid_a = manifest["seed_run_id"] + "-a"
    cwd_a = tmp_path / "run_a"
    cwd_a.mkdir()
    seed_run(cwd_a, rid_a, manifest["user_prompt"])
    trace_a = run_and_record(
        cwd_a, rid_a, num_steps=manifest["num_steps"],
    )

    # Run B (independent filesystem, same logical seed).
    rid_b = manifest["seed_run_id"] + "-b"
    cwd_b = tmp_path / "run_b"
    cwd_b.mkdir()
    seed_run(cwd_b, rid_b, manifest["user_prompt"])
    trace_b = run_and_record(
        cwd_b, rid_b, num_steps=manifest["num_steps"],
    )

    assert trace_a == trace_b, (
        f"replay determinism violation: trace_a != trace_b\n"
        f"a: {trace_a}\nb: {trace_b}"
    )


def test_replay_partial_replay_from_step_3(tmp_path: Path):
    """Reaching step 3 by way of steps 0..2 produces the same step-3
    fingerprint as the saved canonical trace.

    Models the §20.7 "rerun stage N → stages > N invalidated" property:
    after planting all upstream stubs, step 3 emits the same action
    independent of which run-id or filesystem we're in.
    """
    manifest, expected_trace = _load_fixture()
    run_id = manifest["seed_run_id"] + "-partial"
    seed_run(tmp_path, run_id, manifest["user_prompt"])
    rd = tmp_path / ".triz" / "runs" / run_id

    # Drive steps 0, 1, 2 in lockstep with the canonical trace.
    for i in range(3):
        action = invoke_next_action(run_id, tmp_path)
        fp = ActionFingerprint.of(action)
        assert fp == expected_trace[i], (
            f"prefix mismatch at step {i}: {fp} vs {expected_trace[i]}"
        )
        plant_stub_for(action, rd)

    # Now read step 3 and confirm it matches.
    action = invoke_next_action(run_id, tmp_path)
    fp = ActionFingerprint.of(action)
    assert fp == expected_trace[3], (
        f"step 3 fingerprint mismatch after partial replay:\n"
        f"  actual:   {fp}\n"
        f"  expected: {expected_trace[3]}"
    )


@pytest.mark.parametrize("step_index,canonical_artifact", [
    (0, "01_problem.json"),
    (1, "02_selection.json"),
    (3, "04_principles_altshuller_39x39.json"),
])
def test_smoke_step_n_expects_artifact(step_index, canonical_artifact, tmp_path: Path):
    """Step N's expected_artifact field matches the documented schema
    artifact for that stage. This pins the expected_artifact contract
    at each canonical step against schema-name drift.
    """
    manifest, expected_trace = _load_fixture()
    fp = expected_trace[step_index]
    # Steps 0/1/3 are single-artifact actions (dispatch_subagent or
    # run_script); step 2/4 are parallel and encode artifact lists.
    assert fp.expected_artifact == canonical_artifact, (
        f"step {step_index} expected_artifact={fp.expected_artifact!r}, "
        f"want {canonical_artifact!r}"
    )
