# Fixture: 04_selection-no-tiebreak

**Kind:** states
**Description:** 02_selection.json with stage_e_invoked=false. Expect mapping_phase1 dispatch.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-04-sel-no-e`
