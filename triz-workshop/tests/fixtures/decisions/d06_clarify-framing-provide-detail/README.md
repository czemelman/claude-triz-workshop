# Fixture: d06_clarify-framing-provide-detail

**Kind:** decisions
**Description:** User chooses provide_clarification to refine a low-confidence framing. The decision handler appends the clarification to constraints[] and resets stage to FRAMER. Because the underlying 01_problem.json still validates, the subsequent stage check sees framing_confidence=low and re-emits ask_user clarify_framing — a defensible loop until the framer is re-dispatched (i.e. 01_problem.json is removed). The expected.json captures the actual current behavior; the brief's idealized 'dispatch framer' shape is not yet reachable from this input alone.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-d06-clarify-detail`
