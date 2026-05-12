# Fixture: 22_critique-all-fatal

**Kind:** states
**Description:** 07_critique with all fatal. Expect ask_user WITHOUT drop_fatal_proceed.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-22-crit-all-fatal`
