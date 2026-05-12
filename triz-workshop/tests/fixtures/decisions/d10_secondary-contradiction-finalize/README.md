# Fixture: d10_secondary-contradiction-finalize

**Kind:** decisions
**Description:** User offers a 'secondary_contradiction_finalize' choice (per design wording, finalize without iterating).

Behavior gap vs design: this choice is NOT implemented; current code returns self_correct.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d10-finalize`
