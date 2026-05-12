# Fixture: 24_secondary-contradiction-loop-iteration-2

**Kind:** states
**Description:** Same as fixture 23 but loop_depth=2 (would be the 3rd iteration if loops were implemented).

Behavior gap: secondary-contradiction loop iteration is unimplemented; state-driver advances to assemble regardless of loop_depth when no fatal candidates exist.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-24-loop-iter-2`
