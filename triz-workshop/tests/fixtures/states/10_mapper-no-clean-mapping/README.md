# Fixture: 10_mapper-no-clean-mapping

**Kind:** states
**Description:** Mapper says no_clean_mapping=true. Branch to no-resolution.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-10-mapper-noclean`
