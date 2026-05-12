# prizm eval harness

This directory implements the v0.1 eval harness described in design v6 §21.

## v0.1 SYNTHETIC vs Phase 2 LIVE

The v0.1 runner is intentionally **synthetic**. When `next_action.py` emits
a `dispatch_subagent` action, the runner writes a schema-valid stub artifact
and continues — it does NOT call any LLM subagent. Live LLM dispatch is
expensive, non-deterministic, and depends on the Claude Code runtime; v0.1
eval measures the *deterministic routing layer* of the plugin, not LLM
output quality.

| Metric | v0.1 SYNTHETIC | Phase 2 LIVE |
|---|---|---|
| `branch_reached` (normal / low_framing_confidence / no_clean_mapping) | YES — measured against `expected_branch` | YES |
| `selected_matrix` matches `expected_matrix_id` | Diagnostic only — selector input is a stub problem, not real LLM framing | YES — measured |
| `param_pair` matches `expected_param_pair` | Diagnostic only — stubs use defaults | YES — measured |
| `principle_jaccard` against `accepted_principles` | Diagnostic only | YES — measured |
| Critic shared-blind-spot rate (§21.3a) | Not measured (no LLM critic) | YES |
| Heterogeneity routing accuracy (§21.3a) | Partial — `branch_reached` is checked | YES |

**Bottom line:** if v0.1 SYNTHETIC says `branch_reached` is correct, the
state-driver routing is sound. If `selected_matrix` is wrong, that's
typically because the stub framer doesn't carry the real problem's signals
into Stage A scoring — a Phase 2 framer would fix that.

## File layout

```
eval/
    run_eval.py                        # Runner (this dir's main entry point)
    labeled_problems.public.jsonl      # 10 v6 §21.2 cases (committed)
    labeled_problems.local.jsonl       # Optional: developer-local cases (gitignored)
    reports/                           # Auto-generated; gitignored
        <UTC-timestamp>.md
    README.md                          # This file
    .gitignore
```

## Running it

```bash
# From the plugin root, with the corpus reachable:
TRIZ_MATRICES_PATH=$(realpath ..) python3 eval/run_eval.py

# Include developer-local cases too:
TRIZ_MATRICES_PATH=$(realpath ..) python3 eval/run_eval.py --include-local

# Print the report to stdout in addition to the file:
TRIZ_MATRICES_PATH=$(realpath ..) python3 eval/run_eval.py --report-stdout
```

The runner prints per-case `[OK]` / `[MISS]` markers as it goes and writes
`reports/<UTC-timestamp>.md` with a summary table and per-case action
traces.

## Labeled-case format

Each line of `labeled_problems.public.jsonl` is one JSON object. Required
fields:

- `case_id` — unique identifier (`norm_NNN_*`, `low_NNN_*`, `ncm_NNN_*` by
  convention).
- `problem_statement` — the user's free-text problem; passed to
  `next_action.py --new-run --user-prompt`.
- `expected_branch` — one of `normal`, `low_framing_confidence`,
  `no_clean_mapping`.

Optional fields (used for the additional diagnostic metrics; omit for
low/ncm cases where they don't apply):

- `expected_matrix_id` — id from `registry.json` you expect the selector
  to pick (e.g. `altshuller_39x39`).
- `expected_param_pair` — `[improving_param_id, worsening_param_id]` in
  the host matrix's native id space (numeric strings, prefixed S/T, etc).
- `accepted_principles` — array of integer principle ids the cell should
  return; used for the Jaccard score.
- `domain_class` — one of the values in
  `selector_tags_vocabulary.json:domain_classes`. Used by the synthetic
  framer to set `01_problem.json:domain_class`.
- `domain_signals` — explicit override of the framer's `domain_signals`
  array (otherwise inferred from `domain_class`).
- `exotic_signals` — same, for `exotic_signals`.
- `notes` — free-text rationale for human readers.

## Adding a new case

1. Pick a `case_id` matching the convention.
2. Add a JSON line to `labeled_problems.public.jsonl` (or `.local.jsonl`
   for unshared cases).
3. Run `python3 eval/run_eval.py` and inspect the resulting report.
4. If your case's `branch_reached` doesn't match `expected_branch`, debug
   by reading the per-case action trace in the report — it shows every
   `dispatch_*` / `run_script` / `ask_user` / `done` step the state-driver
   emitted.

## Branch-coverage breakdown (v6 §21.2)

The current 10 public cases are split:

- 6 `normal` (multi-domain: mechanical, software, governance, healthcare,
  bio, aerospace)
- 2 `low_framing_confidence` (vague / non-engineering prompts)
- 2 `no_clean_mapping` (aesthetic / creative-writing prompts that no
  matrix can serve)

When ≥30 labeled cases are available the eval will be re-run with the
weights-calibration grid search (design v6 §11.2) to graduate
`weights_version` from `v0` to `v1`.

## How the synthetic stubs work

When `next_action.py` emits `dispatch_subagent`, the runner picks a stub
factory by subagent name:

| subagent | stub artifact written |
|---|---|
| `triz-problem-framer` | `01_problem.json` with framing_confidence keyed off `expected_branch` |
| `triz-parameter-mapper` | `03_mapping_<matrix>.json` |
| `triz-mapping-critic` | `03c_independent_mapping_<matrix>.json` (Phase 1) or `03b_mapping_critique_<matrix>.json` (Phase 2) |
| `triz-principle-interpreter` | `05_interpretation_<matrix>_<pid>.json` |
| `triz-solution-synthesizer` | `06_solutions.json` |
| `triz-solution-critic` / `triz-contradiction-critic` | `07_critique.json` |
| `triz-matrix-selector` (Stage E tiebreak) | mutates `02_selection.json` to set `stage_e_invoked=true` |

For `run_script` actions (selector, lookup, merge, assemble), the runner
shell-executes the in-tree Python script with the same args the state
driver requested. This means **the eval harness exercises the real
selector / lookup / merge / assemble logic** — it's only the LLM
subagents that are stubbed.

## Phase 2 plans

A `--live` flag will call subagents through the Claude Code runtime and
measure:

- shared-blind-spot rate (§21.3a)
- cross-matrix angle preservation (§21.3a)
- heterogeneity routing accuracy (§21.3a)

Phase 2 also expands `labeled_problems.public.jsonl` to ≥30 cases for
the weights calibration step (§11.2).
