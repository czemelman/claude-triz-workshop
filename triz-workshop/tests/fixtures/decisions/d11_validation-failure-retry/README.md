# Fixture: d11_validation-failure-retry

**Kind:** decisions
**Description:** User chooses edit_artifact; retry budget remains. Driver re-dispatches the framer subagent.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d11-validation-retry`
