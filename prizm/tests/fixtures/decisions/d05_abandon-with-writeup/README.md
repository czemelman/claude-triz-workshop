# Fixture: d05_abandon-with-writeup

**Kind:** decisions
**Description:** User abandons; expect run_script assemble_report --no_resolution.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d05-abandon-writeup`
