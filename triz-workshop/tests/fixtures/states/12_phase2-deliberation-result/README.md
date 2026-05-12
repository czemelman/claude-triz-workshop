# Fixture: 12_phase2-deliberation-result

**Kind:** states
**Description:** Phase 2 critic wrote 03b_mapping_critique_*.json with verdict=disagree (override). State driver advances to lookup; next action is run_script lookup_principles using the resolved (chosen) mapping.

## Layout

- `state/` — files copied verbatim into `.triz/runs/<run-id>/` before invoking `next_action.py`.
- `invocation.json` — args (and optional user_input) passed to next_action.py.
- `expected.json` — the action `next_action.py` is expected to emit on stdout.

## Run id
`fix-12-phase2-result`
