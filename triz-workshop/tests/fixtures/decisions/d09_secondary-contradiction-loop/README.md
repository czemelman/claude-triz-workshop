# Fixture: d09_secondary-contradiction-loop

**Kind:** decisions
**Description:** User offers a 'secondary_contradiction_loop' choice (per design wording).

Behavior gap vs design: this choice is NOT implemented in _apply_user_decision. Current code returns self_correct with 'unknown user decision choice'. Documenting v0.1 reality.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d09-loop`
