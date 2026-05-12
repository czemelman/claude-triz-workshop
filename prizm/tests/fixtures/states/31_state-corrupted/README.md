# Fixture: 31_state-corrupted

**Kind:** states
**Description:** state.json is malformed (invalid JSON). Expect ask_user kind=state_corrupted with options abort, attempt_repair.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-31-state-corrupt`
