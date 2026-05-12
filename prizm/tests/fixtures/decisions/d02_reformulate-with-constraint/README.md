# Fixture: d02_reformulate-with-constraint

**Kind:** decisions
**Description:** User adds constraint and re-synthesizes. State resets to synthesize.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d02-reformulate`
