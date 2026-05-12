# Fixture: 32_argparse-missing-run-id

**Kind:** states
**Description:** Closest integration-runner-compatible variant of 'missing --run-id'.

args = ['--new-run'] with no --user-prompt. The fixture loader treats this as a new run (run_id='<new>'). Current code accepts this and emits a normal framer dispatch with empty user_prompt. The strict 'missing --run-id and not --new-run' invocation is NOT loadable by install_fixture; that case is covered by tests/unit/test_argparse_hardening.py.

Behavior gap vs design: the design wording suggested self_correct for this seam, but current code does not require --user-prompt with --new-run.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`<new>`
