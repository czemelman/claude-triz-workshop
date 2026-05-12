# Fixture: 06_selection-empty-result

**Kind:** states
**Description:** Selection script returned 0 candidates (invalid per schema). retry_counts.select_matrix at cap; expect ask_user stage_retry_exhausted.

Note: the design wording 'expect ask_user' for this case maps to stage_retry_exhausted in current code, since the schema requires selected_matrices.minItems=1 — an empty selection always fails validation, never reaches the no_matrices_selected branch.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-06-sel-empty`
