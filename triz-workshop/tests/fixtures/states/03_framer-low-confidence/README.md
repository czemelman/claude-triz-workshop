# Fixture: 03_framer-low-confidence

**Kind:** states
**Description:** 01_problem.json with framing_confidence=low. Expect ask_user clarify_framing.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-03-framer-low`
