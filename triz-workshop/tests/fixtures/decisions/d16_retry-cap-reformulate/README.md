# Fixture: d16_retry-cap-reformulate

**Kind:** decisions
**Description:** At retry cap (framer at 3), user chose reformulate_with_constraint with constraint_text.

Behavior gap vs design: design wording said 'framer re-dispatch with reset state'. Actual code: reformulate_with_constraint appends the constraint to 01_problem, sets current_stage=synthesize, deletes 06_solutions/07_critique/final-report (but NOT mapping/lookup artifacts), and dispatches the solution-synthesizer (since 06_solutions is gone). Documenting v0.1 reality.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d16-reform`
