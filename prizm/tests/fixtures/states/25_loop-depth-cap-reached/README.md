# Fixture: 25_loop-depth-cap-reached

**Kind:** states
**Description:** loop_depth equals max_loops (cap reached). Per design: should ask_user or assemble.

Actual current code: state-driver doesn't track loop_depth in any branch — assemble runs whenever no fatal candidates exist, regardless of loop_depth. Documenting v0.1 behavior.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-25-loop-cap`
