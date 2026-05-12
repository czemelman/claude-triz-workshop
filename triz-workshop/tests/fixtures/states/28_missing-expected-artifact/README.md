# Fixture: 28_missing-expected-artifact

**Kind:** states
**Description:** Subagent failed to write the expected artifact (01_problem.json absent). retry_counts.framer=3 (at cap, bump to 4 > MAX_RETRIES_PER_STAGE). Expect ask_user kind=stage_retry_exhausted.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-28-missing-art`
