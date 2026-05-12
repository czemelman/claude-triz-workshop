# Fixture: 16_interpret-8-principles-batch-1

**Kind:** states
**Description:** 8 principles, none done. Expect dispatch_subagents_parallel (action contains 8 dispatches; orchestrator chunks by batch_size=7).

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-16-interpret-8-b1`
