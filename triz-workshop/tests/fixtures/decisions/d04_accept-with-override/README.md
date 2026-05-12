# Fixture: d04_accept-with-override

**Kind:** decisions
**Description:** User chose accept_with_override at fatal_severity_in_critique. State-driver sets flags.override_logged and routes to assemble_report.py with --override_logged.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d04-accept-ovr`
