# Fixture: d08_clarify-framing-abandon

**Kind:** decisions
**Description:** User aborts at framing-clarify. Expect run_script assemble_report --no_resolution.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d08-clarify-abandon`
