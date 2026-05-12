---
description: Re-run a prior `/prizm:solve` from its cached artifacts. Takes a run id as $ARGUMENTS plus optional `--from=<stage>`, `--rerun-only=<stage>`, `--use-current-registry`. Cascade invalidation is handled by the script — your job is the same dispatcher loop as prizm:solve.
allowed-tools: Task, Bash, Read, Write
---

You are the dispatcher for `/prizm:replay`. The state-driver `next_action.py` handles replay semantics (cascade invalidation, snapshot-vs-current-registry decisions, `--from`/`--rerun-only` reconstruction). You do not — your loop is identical to `/prizm:solve`.

## Loop

1. **First call.** Parse `$ARGUMENTS` as `<run-id> [--from=<stage>] [--rerun-only=<stage>] [--use-current-registry]`. Run:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/next_action.py --replay-from <run-id> \
       [--from=<stage>] [--rerun-only=<stage>] [--use-current-registry]
   ```
   Subsequent calls drop the replay flags and just pass `--run-id <run-id>` (and `--user-input '<json>'` when answering an `ask_user`).

2. **Parse stdout** as one JSON object. Stderr is empty; exit code is always 0.

3. **Dispatch the one action** by its `action` field, then loop.

4. **Repeat until** `action == "done"`, then surface `report_path` and stop.

## Action handlers

Identical to `/prizm:solve`:

- **`dispatch_subagent`** — Task call with `prompt`; subagent writes `expected_artifact`.
- **`dispatch_subagents_parallel`** — All `dispatches` as parallel Task calls; honor `batch_size` if present.
- **`run_script`** — `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/<script>` with the supplied `args`.
- **`ask_user`** — Present the `kind`, context, and `options`; pass the user's answer back via `--user-input` next iteration. Stale-registry replay specifically may emit `kind: "stale_registry"` with options `migrate_to_new_id`, `abort_replay`, `proceed_with_snapshot` — pass the choice through verbatim.
- **`self_correct`** — Read `message` and `hint`, fix the invocation, retry once.
- **`done`** — Surface `report_path` and stop.
