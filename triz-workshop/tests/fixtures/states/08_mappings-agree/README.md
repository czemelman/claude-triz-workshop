# Fixture: 08_mappings-agree

**Kind:** states
**Description:** Mapper and critic agree (both 9,14). Expect run_script lookup_principles.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-08-map-agree`
