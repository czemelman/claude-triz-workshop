# Fixture: 27_validation-failure-mid-pipeline

**Kind:** states
**Description:** The most recent artifact (01_problem.json) fails schema validation. retry_counts.framer=2 → will bump to 3 (still under MAX_RETRIES_PER_STAGE=3 cap, so re-dispatch). Expect dispatch_subagent triz-problem-framer.

Note: the state-driver only schema-validates 01_problem and 02_selection between stages. Mid-pipeline schema failures (e.g. invalid 06_solutions.json) would NOT be caught — that's a behavior gap vs design wording.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-27-validation-fail`
