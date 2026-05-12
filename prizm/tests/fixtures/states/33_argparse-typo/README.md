# Fixture: 33_argparse-typo

**Kind:** states
**Description:** args contain a typo `--runid` AND a valid `--run-id` (so the fixture loader can extract a run_id for state copy). argparse sees the unrecognized `--runid` flag and emits a self_correct.

Note: the integration runner (test_routing_fixtures.py) requires the loader to find a run_id; pure 'missing --run-id' invocations are tested in tests/unit/test_argparse_hardening.py instead.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-33-argparse-typo`
