# Fixture: 34_argparse-extra-args

**Kind:** states
**Description:** args include unexpected positional arguments after the valid `--run-id`. argparse rejects positionals → self_correct.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-34-argparse-extra`
