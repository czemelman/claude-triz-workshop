# Fixture: 09_mappings-disagree

**Kind:** states
**Description:** Mapper and critic disagree (different axes). Expect Phase-2 critic dispatch.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-09-map-disagree`
