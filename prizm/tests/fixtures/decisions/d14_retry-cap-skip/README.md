# Fixture: d14_retry-cap-skip

**Kind:** decisions
**Description:** At retry cap, user chose 'skip' / 'skip_stage'.

Behavior gap: not implemented; current code returns self_correct.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d14-skip`
