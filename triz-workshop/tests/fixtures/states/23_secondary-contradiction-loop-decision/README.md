# Fixture: 23_secondary-contradiction-loop-decision

**Kind:** states
**Description:** 07_critique has secondary_contradictions (no fatal severity). User opted into auto-loop (flags.auto_loop=true).

Behavior gap vs design: the state-driver's _stage_check_fatal only inspects severity=='fatal' and ignores secondary_contradictions for loop iteration. With no fatal candidates, it advances directly to assemble. The 'loop iteration' branch is unimplemented in v0.1.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-23-secondary-loop`
