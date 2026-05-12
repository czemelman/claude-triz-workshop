# Fixture: 01_init-empty-run

**Kind:** states
**Description:** First call after --new-run with no prior state. Expect framer dispatch.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`<new>`
