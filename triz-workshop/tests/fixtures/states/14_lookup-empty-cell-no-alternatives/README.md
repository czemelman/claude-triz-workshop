# Fixture: 14_lookup-empty-cell-no-alternatives

**Kind:** states
**Description:** lookup_principles found no populated cell and no alternative populated. populated=false; state-driver branches to no_resolution → assemble report with --no_resolution.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-14-lookup-empty`
