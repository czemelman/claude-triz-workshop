# Fixture: d12_validation-failure-skip

**Kind:** decisions
**Description:** User chose 'skip' (skip the failed stage) per design wording at validation-failure ask_user.

Behavior gap: 'skip' / 'skip_stage' is NOT a recognized choice. Current code returns self_correct.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d12-skip`
