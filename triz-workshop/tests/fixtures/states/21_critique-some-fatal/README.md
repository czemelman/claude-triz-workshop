# Fixture: 21_critique-some-fatal

**Kind:** states
**Description:** 07_critique with one fatal of two. Expect ask_user including drop_fatal_proceed AND abandon_with_writeup.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-21-crit-some-fatal`
