# Fixture: d15_retry-cap-abandon

**Kind:** decisions
**Description:** At retry cap (framer at 3), user chose abandon_with_writeup. State-driver sets flags.no_resolution and routes to assemble_report.py with --no_resolution; final-report.md will be a 'no acceptable resolution' writeup.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d15-abandon`
