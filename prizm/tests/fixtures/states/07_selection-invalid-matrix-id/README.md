# Fixture: 07_selection-invalid-matrix-id

**Kind:** states
**Description:** Selection lists a matrix_id not in the registry. Current code does NOT self-correct — it dispatches mapper+critic for the bogus id. (Behavior gap vs design: the design said 'expect self_correct or ask_user' but the state driver has no registry-validation step at this seam.)

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-07-sel-bad-id`
