# Fixture: d01_drop-fatal-proceed

**Kind:** decisions
**Description:** User chooses drop_fatal_proceed. Expect run_script assemble_report.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d01-drop-fatal`
