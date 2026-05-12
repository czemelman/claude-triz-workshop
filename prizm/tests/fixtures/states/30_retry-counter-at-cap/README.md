# Fixture: 30_retry-counter-at-cap

**Kind:** states
**Description:** retry_counts.framer=3 (== MAX_RETRIES_PER_STAGE). Next bump → 4 > cap, triggers ask_user kind=stage_retry_exhausted. retry_subagent is NOT in the offered options because the design's option list at this seam only covers abort + edit_artifact.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-30-retry-cap`
