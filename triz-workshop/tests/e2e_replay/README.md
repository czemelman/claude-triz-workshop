# E2E Replay Regression Tests

Implements design v6 §20.7 (Layer 4 — End-to-end replay regression).

## What this is

A regression-test corpus where each fixture is a recorded trace of the
state-driver's action sequence on a canonical happy-path run. The test
re-runs the same sequence and asserts the action stream is identical.
Drift in `next_action.py` shows up as a fingerprint mismatch at the
exact step where the new behavior diverges.

The §20.7 vision is "anonymized real runs accumulate as long-form
regression tests." This directory ships the **seed**: a synthetic
5-step trace based on the canonical heat-exchanger eval case
(`norm_001_heat_exchanger`, `expected_branch: normal`,
`altshuller_39x39`).

## Layout

```
tests/e2e_replay/
    __init__.py
    _runner.py              -- shared replay-driver helpers
    test_replay_smoke.py    -- the smoke test
    fixtures/
        heat_exchanger_smoke/
            manifest.json       -- describes the run + the seed state
            trace_actions.jsonl -- recorded action fingerprints (one per line)
```

## Adding a new fixture

When a real production run finishes successfully and the run is worth
locking in as a regression baseline:

1. Anonymize the user prompt (strip identifying details; keep enough
   context that the contradiction still routes the same way).
2. Pick a stable `fixture_id` and run-id (e.g. the eval-case id, plus
   a `_real` suffix to distinguish from synthetic seeds).
3. Drop the run's `01_problem.json` … final-report.md sequence into
   `fixtures/<fixture_id>/`. Optionally include the `state.json` from
   each consult.
4. Record the action trace by re-driving `next_action.py` against the
   real artifacts and writing each fingerprint to
   `trace_actions.jsonl`. The `_runner.run_and_record` helper does
   exactly this when given a pre-populated run-dir; just disable
   `plant_stub_for` if the artifacts are already authentic.
5. Add a `manifest.json` describing the run.
6. Commit the whole directory under `fixtures/`. Add a parameterized
   case to `test_replay_smoke.py` so the new fixture is exercised by
   default.

## What's a "fingerprint"?

Defined in `_runner.ActionFingerprint`. It strips run-id-encoded prompt
text and other free-form fields, keeping only the structural identity
of an action: `action`, `script`, `subagent`, `kind`,
`expected_artifact`, the list of expected artifacts (for parallel
dispatches), and the `(subagent, expected_artifact)` pairs.

Two actions with the same fingerprint are the "same" action for
replay-equivalence. Two runs that produce the same fingerprint sequence
are equivalent runs.

## Why a smoke test, not a full replay yet?

A full replay implementation needs `next_action.py --replay-from`
support — the flag is parsed today but the cascade-invalidation logic
is unimplemented. Once that ships, this test can be extended to drive
the same fixture end-to-end via `--replay-from` and assert identical
fingerprints for `--replay-from <stage>` from any step in the trace.

For now the smoke test gives us:

- A baseline regression check (the action sequence matches what was
  recorded yesterday).
- Replay-determinism (two independent runs of the same seed produce
  the same trace).
- Partial-prefix replay (reaching step N and reading step N+1 matches
  the canonical trace).

When the real `--replay-from` flag is wired up, these scaffolds become
real-replay regression tests with no scaffolding rewrite required.
