---
description: Pretty-print one matrix's registry metadata and use-case file for human reading. Takes a single matrix id as $ARGUMENTS.
allowed-tools: Read
---

You are the dispatcher for `/prizm:explain`. This is a read-only metadata printer — no subagents, no scripts, no state.

## Steps

1. **Read $ARGUMENTS** as a single matrix id (trim whitespace; ignore everything after the first token). If empty, ask the user to supply a matrix id and stop.

2. **Resolve the registry path** as `${TRIZ_MATRICES_PATH}/registry.json` (default `${CLAUDE_PLUGIN_ROOT}/../registry.json`) and Read it. Find the matrix entry whose `id` matches `$ARGUMENTS`. If no entry matches, list the available ids and stop.

3. **Read the matrix's use-case file** at the registry entry's `use_case_file` path (relative to the matrices root). Skip this step if `use_case_file` is null.

4. **Render the output as a markdown document** with these sections — omit any section whose source data is missing:

   ### `<id>`
   - One-line summary from the registry entry's `summary`.

   ### Registry metadata
   - `status`, `language`, `dimensions` (rows × cols, populated_cells), `parameter_id_style`, `diagonal_cells`, `principle_taxonomy`, `interpretation_lineage`, `content_hash`, `lineage` (derived_from / supersedes / identical_to).

   ### What it is
   - The use-case file's `what_it_is` paragraph.

   ### When to use
   - `ideal_user_profile` (one paragraph).
   - `best_for` as a bulleted list.
   - `not_suitable_for` as a bulleted list.
   - `prefer_over_alternatives_when` (one paragraph).

   ### Selector tags
   - `domains`, `problem_classes`, `tags`, `excludes` — one bullet per group with the values comma-separated.

   ### Skip-in-favor-of redirects
   - One bullet per `skip_in_favor_of[]` entry: target id and a plain-language summary of the `if` predicate (e.g. `if exotic_signal == "bio-analogy"`, `if all_of [domain_signal == "pharmaceutical", exotic_signal == "governance"]`).

   ### Coverage and strengths/weaknesses
   - Top 3 `strengths` and top 3 `weaknesses` (only the `area` headlines).

5. Stop after printing. No follow-up actions.
