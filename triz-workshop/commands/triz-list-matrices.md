---
description: List every matrix in the registry as a markdown table. Read-only; no subagent dispatch. Optional filters parsed from $ARGUMENTS — `--domain=<id>`, `--status=<canonical|domain|variant|derived|experimental|shell|identical-duplicate>`, `--tag=<tag>`. Shell matrices are listed with a `(no cell data)` flag.
allowed-tools: Bash, Read
---

You are the dispatcher for `/triz-workshop:triz-list-matrices`. This is a read-only registry inspector — no subagents, no run dir, no state changes.

## Steps

1. **Resolve the registry path.** Use `${TRIZ_MATRICES_PATH}/registry.json` if the env var is set, otherwise the project default `${CLAUDE_PLUGIN_ROOT}/../registry.json`. Read the file with the Read tool.

2. **Parse `$ARGUMENTS`** for optional filters (any of the three; all may be combined; an absent filter matches everything):
   - `--domain=<value>` — keep only matrices whose `use_cases/<id>.json:selector_tags.domains` array contains `<value>`.
   - `--status=<value>` — keep only matrices whose registry `status` equals `<value>`.
   - `--tag=<value>` — keep only matrices whose `use_cases/<id>.json:selector_tags.tags` array contains `<value>`.

3. **For each matching matrix**, read its `use_case_file` from the registry entry (skip silently if the file is absent — some redundant entries have none) to pull the top tags. Skip the file read for matrices whose registry status is `shell` or whose `use_case_file` is null.

4. **Print one markdown table** with these columns, one row per matrix, sorted by registry order:

   | id | status | dimensions | summary | top tags |

   - `id` from the registry entry.
   - `status` from the registry entry. If `shell`, append ` (no cell data)`.
   - `dimensions` formatted as `rows×cols, populated_cells` from `dimensions`.
   - `summary` from the registry entry's `summary`, truncated to ~80 chars.
   - `top tags` is the first 4 entries of `selector_tags.tags` joined by `, ` — or `—` if no use case file is present.

5. **Append a one-line footer** giving the total count and any active filters, e.g. `12 matrices (filter: status=domain)`. Stop.
