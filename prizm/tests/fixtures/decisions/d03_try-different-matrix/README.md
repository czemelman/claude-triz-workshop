# Fixture: d03_try-different-matrix

**Kind:** decisions
**Description:** User chose try_different_matrix at fatal_severity_in_critique with matrix_id='heinrich_39x39'. State-driver wipes selection-and-downward artifacts and re-dispatches select_matrix.py with --matrix heinrich_39x39 forced.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d03-try-mat`
