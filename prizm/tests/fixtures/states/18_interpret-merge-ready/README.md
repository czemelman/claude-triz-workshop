# Fixture: 18_interpret-merge-ready

**Kind:** states
**Description:** All per-principle artifacts written. Expect run_script merge_interpretations.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-18-interpret-merge`
