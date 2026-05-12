# Fixture: d07_clarify-framing-proceed-anyway

**Kind:** decisions
**Description:** User accepts low-confidence framing. Expect run_script select_matrix.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d07-clarify-proceed`
