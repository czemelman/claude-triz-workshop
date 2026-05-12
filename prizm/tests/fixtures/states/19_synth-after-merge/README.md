# Fixture: 19_synth-after-merge

**Kind:** states
**Description:** 05_interpretations.json exists; no 06_solutions yet. Expect dispatch_subagent triz-solution-synthesizer.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-19-synth-after-merge`
