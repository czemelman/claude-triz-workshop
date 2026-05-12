# Fixture: 29_retry-counter-at-2

**Kind:** states
**Description:** retry_counts.framer=2; bump to 3 which equals MAX_RETRIES_PER_STAGE. The cap check is `retries > MAX_RETRIES_PER_STAGE`, so 3 still permits one more dispatch. Expect dispatch_subagent triz-problem-framer.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-29-retry-at-2`
