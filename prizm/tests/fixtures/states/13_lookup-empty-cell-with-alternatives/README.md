# Fixture: 13_lookup-empty-cell-with-alternatives

**Kind:** states
**Description:** lookup_principles fell back to an alternative (primary cell empty, alternative populated). 04_principles populated=true via alternatives_tried[1]. Expect interpret-stage dispatch.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-13-lookup-alt`
