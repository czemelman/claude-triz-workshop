# triz-workshop — Complete Plugin Design (v6, consolidated)

**Date:** 2026-05-04
**Status:** Canonical design. Supersedes v1, v2, v3, v4, v5.
**Companion:** `matrix_storage_design.md` v1.1 (the matrix-collection schema this design depends on, including amendments 1–5).

This is the unified, current design for `triz-workshop`, a Claude Code plugin that turns a TRIZ matrix collection into a working contradiction-resolution pipeline. It is the single document you need to read; prior versions are historical and can be discarded.

The design has been through four adversarial reviews. Each round shaped a structural decision that's now baked in: the mapping-critic pattern (review 1), the state-driver inversion (review 2), the testing strategy (review 3), and **matrix-corpus heterogeneity handling plus Phase-0 elevation (review 4)**. The reasoning behind each is preserved here so future readers know why things are shaped the way they are.

---

## Document map

1. [TL;DR](#1-tldr)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [Architectural Principles](#3-architectural-principles)
4. [Claude Code Primitives — What We Use, What We Don't](#4-claude-code-primitives--what-we-use-what-we-dont)
5. [Component Inventory](#5-component-inventory)
6. [The State-Driver Pattern](#6-the-state-driver-pattern)
7. [End-to-End Workflow](#7-end-to-end-workflow)
8. [Slash Commands](#8-slash-commands)
9. [Subagents](#9-subagents)
10. [Deterministic Scripts](#10-deterministic-scripts)
11. [The Methodology Skill](#11-the-methodology-skill)
12. [Validation Hooks](#12-validation-hooks)
13. [Artifact Schemas](#13-artifact-schemas)
14. [Matrix Selection Algorithm](#14-matrix-selection-algorithm)
15. [Two-Phase Mapping Critic](#15-two-phase-mapping-critic)
16. [No-Clean-Mapping Branch](#16-no-clean-mapping-branch)
17. [Fatal-Severity Flow](#17-fatal-severity-flow)
18. [Run Artifacts, Replay, Manifest](#18-run-artifacts-replay-manifest)
19. [Argparse Hardening & Retry Counters](#19-argparse-hardening--retry-counters)
20. [Testing Strategy](#20-testing-strategy)
21. [Eval Harness](#21-eval-harness)
22. [Failure Modes & Recovery](#22-failure-modes--recovery)
23. [Configuration Surface](#23-configuration-surface)
24. [Three-Axis Versioning](#24-three-axis-versioning)
25. [Plugin Layout & Distribution](#25-plugin-layout--distribution)
26. [Phasing](#26-phasing)
27. [Open Questions & Acknowledged Risks](#27-open-questions--acknowledged-risks)
28. [Why This Design Looks Like This](#28-why-this-design-looks-like-this)

Appendices: [A. Sample Run](#appendix-a--sample-run) · [B. LLM's Chat Context](#appendix-b--what-the-llms-chat-context-actually-looks-like) · [C. Sample Test Fixture](#appendix-c--sample-test-fixture) · [D. Component Cross-Reference](#appendix-d--component-cross-reference) · [E. v5→v6 Changelog](#appendix-e--v5v6-changelog)

---

## 1. TL;DR

A Claude Code plugin with **4 slash commands** (entry points), **7 LLM subagents** (cognitive specialists), **7 deterministic Python scripts** (state machine + symbolic routing + validation + assembly), **1 skill** (TRIZ methodology), **1 PostToolUse hook** (validation safety net writing structured JSON to a log file), and **9 JSON Schemas** (artifact contracts).

The defining architectural choice is the **state-driver pattern**: a Python script `next_action.py` owns the entire state machine. The LLM orchestrator (the parent context running the slash command) is reduced to a small dispatcher loop — it asks the script "what next?", executes the single atomic action it returns, repeats. This eliminates the v3 problem of asking a probabilistic LLM to follow a 17-step procedural runbook reliably across a long context window.

The mapping-critic agent uses **two-phase structural blinding**: the critic produces an independent mapping in Phase 1 with no access to the mapper's output, eliminating anchor bias by construction rather than by prompt instruction. Phase 2 (deliberation) only runs when the two independent mappings disagree.

**v6 changes (review 4 outcomes):**
- Phase 0 (storage migration including amendments 1–5) is now an explicit blocking milestone, not a checklist item.
- The matrix corpus is treated as **heterogeneous by design**: BioTRIZ is split into two matrix ids; shell matrices (Mann) are filtered at Stage A; prefixed-id matrices (healthcare_servqual) and reinterpreted-principle matrices (drug_safety) are tagged in `meta` so the mapper and interpreter can adapt.
- `canonical_id` dedup applies at the principle-list layer only. Interpretations from different `interpretation_lineage`s are kept distinct — collapsing them at the synthesizer eats the cross-matrix triangulation value that motivated multi-matrix runs.
- Selection scoring drops the absolute `coverage_bonus`; coverage is enforced as a Stage A floor instead.
- The `--lang=` flag is removed from v0.1; non-English matrices ship in v1.0+.

Every step writes a numbered JSON artifact to `.triz/runs/<run-id>/`. Schema validation runs both via a hook (writes to log) and via the state-driver before each next-stage dispatch (the actual halt point). Pause points (low framing confidence, mapping disagreement, validation failure, fatal severity, retry-cap reached) all use a single `ask_user` action mechanism with state persisted on disk — kill the run anywhere, resume cleanly.

Selection scoring weights are tagged `weights_version: "v0"` (uncalibrated heuristics) until a labeled eval set produces calibrated `v1` weights. Confidence is categorical (high/medium/low), not scalar — LLMs don't produce calibrated probabilities and pretending they do invites false precision.

The whole system is testable. `next_action.py` is a pure-function-ish state-to-action mapper; 34 state fixtures + 16 decision fixtures + property tests + replay regression cover the full state space with 90% line-coverage as a CI merge gate. A new layer-6 integration test reads the *real* registry to catch fixture/reality drift.

---

## 2. Goals & Non-Goals

### 2.1 Goals

1. **One slash command, end-to-end.** `/triz-workshop:triz-solve "<problem>"` produces ranked solution concepts with full reasoning trace.
2. **Programmatic matrix selection from the registry.** No hardcoding to `altshuller_39x39`. Selection is hybrid: deterministic script does Stages A–D; LLM subagent breaks ties at Stage E.
3. **Multi-matrix triangulation that preserves angle.** When two matrices both fit (e.g. software-payments hits both `triz_ai_50x50` and `altshuller_39x39`), run them in parallel and present their interpretations as distinct angles, not as one deduplicated list.
4. **Auditable trace.** Every step writes a structured artifact. The run is replayable, diff-able, reviewable.
5. **Reliable orchestration.** The LLM never tracks state, never branches conditionally, never validates schemas. A Python script does all of that. The LLM is a dispatcher.
6. **Honest empirical scaffolding.** Selection weights and confidence thresholds are calibrated against a labeled eval set, not authorial intuition. v0 weights are explicitly tagged as such.
7. **First-class "no clean mapping" branch.** Per Souchkov's empirical finding (~10–15% mapping rate), unmappable problems are a normal output state, not an error.
8. **Plugin-shaped from the start.** Component boundaries align with what Claude Code primitives can do, not against them.
9. **Testable to 90% coverage.** The state-driver script is the new system core; an untested state machine isn't a state machine, it's wishful thinking.
10. **Heterogeneity is a first-class concern.** The pipeline does not pretend the matrix corpus is uniform. Per-matrix conventions (prefixed IDs, diagonal cells, reinterpreted principles, dual submatrices, shell matrices) are declared in `meta` and honored by mapper, lookup, and interpreter.

### 2.2 Non-Goals

- Inventing matrices at runtime. Matrix authoring is offline.
- Visual rendering. Output is JSON + markdown.
- Multi-user collaboration.
- Replacing human judgement on principle interpretation.
- Claiming the matrix is the definitive TRIZ tool. Altshuller eventually advised against it in favor of ARIZ; the README will say so.
- Bundling the matrix collection. Matrices version separately and are pointed to via `TRIZ_MATRICES_PATH`.
- Using the Claude Agent SDK or any non-Claude-Code-native dispatch mechanism. Standard Task and Bash tools only.
- Multilingual operation in v0.1. English only ships first; non-English matrices are filtered out by language tag (amendment 4) until `--lang=` lands in v1.0+.

---

## 3. Architectural Principles

1. **Deterministic where possible, LLM where necessary.** Reading a matrix cell, filtering a registry, checking a schema, deciding the next stage — code. Mapping "request authentication latency" to `parameter 9 (Speed)` — LLM. Don't blur the line.
2. **State machine in code, not in chat context.** A Python script (`next_action.py`) consults disk state and emits one atomic action at a time. The LLM executes that single action and asks again. No 17-step runbook for the LLM to drift through.
3. **Subagents own one decision each.** Storm pattern: every subagent has a single job and a single output schema.
4. **Selection before mapping before lookup.** Common failure mode: mapping a problem to `altshuller_39x39` parameters before checking whether `triz_ai_50x50` is a better fit. The pipeline enforces selection-first.
5. **Run artifacts are first-class.** Every step writes its output to disk. Downstream steps load from disk. Subagents start with fresh context windows; the orchestrator must inject artifact paths explicitly.
6. **Fail loud at contracts.** PostToolUse hook validates every artifact; the state-driver validates again before each next-stage dispatch. Belt and suspenders, with the responsibilities clearly split.
7. **No silent fallbacks.** If matrix selection finds nothing matching, the run halts and asks. Does not default to Altshuller.
8. **Calibrated, not intuited.** Numeric thresholds either come from an eval set or are tagged `v0-uncalibrated` so reviewers know what they're looking at.
9. **Categorical confidence everywhere.** LLM-produced 0.0–1.0 confidence values aren't calibrated; thresholding them is false precision. Three buckets (high/medium/low) are honest about the granularity LLMs can actually produce.
10. **Structural blinding beats procedural blinding.** When you need an agent not to be anchored on prior output, don't tell it "ignore X" — physically withhold X from its context.
11. **Pause/resume on disk, not in memory.** Every pause point writes `awaiting_decision.json`. Kill the run; restart from any point via `next_action.py --run-id <id>`. No in-memory orchestrator.
12. **Test the state machine.** The state-driver is the system; an untested state machine produces silent routing bugs that schema validation can't catch.
13. **Heterogeneity is declared, not inferred.** Per-matrix conventions live in `meta` (parameter_id_style, diagonal_cells, principle_taxonomy, language, status). Code branches on declarations, not on filename heuristics.
14. **Cross-matrix angles stay distinct.** Multi-matrix triangulation is valuable because the matrices encode different perspectives. Dedup at the principle-list level (one row in the report per principle); never collapse the interpretations themselves.

---

## 4. Claude Code Primitives — What We Use, What We Don't

Before designing components, mapping which primitives we'll use and why. This shapes every later decision.

### 4.1 What this plugin uses

| Primitive | Used for | Why |
|---|---|---|
| **Slash commands** (`commands/*.md`) | User-facing entry points | Discoverable; namespaced `/<plugin>:<cmd>`; receive raw `$ARGUMENTS` text |
| **Subagents** (`agents/*.md`) | LLM specialists for cognitive steps | Isolated context windows; one job each; output via final-message + on-disk artifact |
| **Deterministic scripts** (`scripts/*.py`, run via Bash) | State machine, selection scoring, cell lookup, validation, merge, report assembly | Fast, testable, deterministic, free of LLM stochasticity |
| **Skills** (`skills/triz-methodology/SKILL.md`) | Background knowledge available to subagents | One source of truth; explicitly listed in each subagent's frontmatter (subagents don't inherit) |
| **Hooks** (`.claude-plugin/plugin.json:hooks.PostToolUse`) | Schema validation safety net writing to log file | Catches drift; not the actual halt point because PostToolUse can't undo writes |
| **Plugin manifest** (`.claude-plugin/plugin.json`) | Metadata, hook config, compatibility declarations | Single source of truth; uninstalls cleanly |

### 4.2 What this plugin deliberately does NOT use

| Primitive | Why we skip it |
|---|---|
| **MCP servers** | Pipeline is self-contained against the matrix collection; adding MCP increases surface area without benefit |
| **WebSearch / WebFetch** | No live web data needed; the matrix is the source of truth |
| **Output styles** | Final report is markdown; no rendering customization needed |
| **PreToolUse hooks** | Pre-validation would block the wrong way; the state-driver's pre-dispatch check is the right place |
| **SessionStart hooks** | No need to inject context at session start; first invocation runs `compatibility_check.py` instead |
| **Stop / Agent / Prompt hooks** | No use case beyond what the orchestrator does; LLM-evaluating artifact validity is the mapping-critic's job |
| **Claude Agent SDK** | Would require external API credentials and break self-containment within Claude Code |

### 4.3 The role of the orchestrator

There is no `triz-orchestrator` subagent. The orchestrator is **the parent context** that runs when the user invokes `/triz-workshop:triz-solve`. It has:

- The Task tool (to dispatch subagents).
- The Bash tool (to run scripts including `next_action.py`).
- Read and Write (to assemble the final report).
- The methodology skill (auto-loaded by description match — it's the parent context, not a subagent).

The orchestrator's instructions live in `commands/triz-solve.md`. Crucially, those instructions are tiny: "call `next_action.py`, do what it says, repeat." No 17-step runbook.

---

## 5. Component Inventory

The complete plugin in one table:

| Component type | Count | Names |
|---|---|---|
| Slash commands | 4 | `triz-solve`, `triz-list-matrices`, `triz-explain-matrix`, `triz-replay` |
| Subagents | 7 | `triz-problem-framer`, `triz-matrix-selector`, `triz-parameter-mapper`, `triz-mapping-critic`, `triz-principle-interpreter`, `triz-solution-synthesizer`, `triz-contradiction-critic` |
| Scripts | 7 | `next_action.py`, `select_matrix.py`, `lookup_principles.py`, `merge_interpretations.py`, `validate_artifact.py`, `compatibility_check.py`, `assemble_report.py` |
| Skills | 1 | `triz-methodology` |
| Hooks | 1 | `PostToolUse` on `Write\|Edit\|MultiEdit` |
| Schemas | 9 | 8 artifact schemas + 1 selector-tag vocabulary |

---

## 6. The State-Driver Pattern

This is the architectural decision that makes everything else hang together. Worth understanding deeply.

### 6.1 What problem this solves

A naive plugin design has the LLM orchestrator follow a procedural runbook from the slash command body: parse flags, dispatch framer, validate output, branch on confidence, dispatch selector, fan out parallel mappers, run critic, route based on verdicts, run loop conditionally, etc. This is asking a probabilistic LLM to act as a deterministic state machine over a long context window. Even Sonnet will skip a validation step, summarize prematurely, or hallucinate a stage transition. Adversarial review correctly identified this as the largest architectural risk.

### 6.2 The pattern

A new deterministic Python script — `scripts/next_action.py` — is the state machine. Each turn, the LLM orchestrator:

1. Calls `next_action.py --run-id <id>` via Bash.
2. Reads back a single JSON object describing **one atomic next action**.
3. Executes that action (via Task, Bash, or surfacing to user).
4. Loops back to step 1.

The LLM never tracks "what stage are we at," "did validation pass," "should we loop." Those are all the script's job. The LLM's entire mental model is: "call the script, do what it says, repeat until it says done."

### 6.3 The action protocol

`next_action.py` outputs exactly one JSON object per call, with one of six action types: `dispatch_subagent`, `dispatch_subagents_parallel`, `run_script`, `ask_user`, `self_correct`, `done`. The protocol is unchanged from v5; see v5 §6.3 for full payload examples.

### 6.4 What `next_action.py` does internally

Pseudocode (unchanged from v5; full version in source):

```python
def main():
    args, err = parse_args_safely(sys.argv[1:])
    if err:
        return emit_self_correct(err)

    try:
        state = State.load_or_create(args.run_id, new=args.new_run)

        if args.user_input:
            state.apply_user_decision(args.user_input)
            state.persist()

        last = state.most_recent_artifact()
        if last and not validate(last):
            return emit_validation_failure(state, last)

        return emit_action_for_stage(state.next_stage(), state)
    except StateCorruptError as e:
        emit_ask_user("state_corrupted", message=str(e), options=["abort", "attempt_repair"])
    except Exception as e:
        emit_self_correct(f"Internal error: {type(e).__name__}: {e}")
```

The script holds the entire state machine. Every conditional, validation, routing decision is here. The LLM never sees any of this.

### 6.5 Why this works without inversion of control or SDK

The LLM is excellent at "given this prompt, dispatch this subagent." It's not excellent at "track 17 stages of nested conditionals." Match the tool to the task: small atomic jobs to LLMs, state machines to code.

### 6.6 What this buys

- **Reliability.** No 17-step runbook for the LLM to drift through. Each LLM turn is a single atomic dispatch.
- **Resumability.** State persists to disk after each transition. Kill anywhere; restart from `next_action.py --run-id <id>`.
- **Testability.** `next_action.py` is unit-testable. Mock the state directory; assert what action it emits. No LLM in the test loop.
- **Cost transparency.** Every LLM call corresponds to one `dispatch_subagent` action. Counting actions = counting LLM calls.
- **Drift recovery.** If the LLM ignores the script and dispatches the wrong thing, the next consultation sees the unexpected/missing artifact and corrects course.

### 6.7 What this costs (honest accounting)

Per stage, one extra Bash round-trip to consult the script. ~50–200ms script execution + ~1–2s API round-trip = ~1.5s per stage of overhead.

For a **single-matrix run with 4 principles**: ~13 LLM calls + ~14 stages = ~21s overhead.

For a **two-matrix run with 8 total principles** (the §7 example flow): ~28 LLM calls and ~20 distinct state-driver stages = ~30s overhead on a ~50s base = **~60% overhead**. Multi-matrix triangulation amplifies this; the per-stage cost is fixed but stage count grows roughly linearly with matrix count.

We accept this. The reliability gain of moving the state machine out of the LLM context is worth it. See §27 for why no current optimization is worth re-introducing the original problem.

---

## 7. End-to-End Workflow

```
USER invokes: /triz-workshop:triz-solve "<problem>" [flags]
  │
  ▼
[LLM ORCHESTRATOR — slash command parent context]
  │
  │  Loop:
  │    1. Bash → next_action.py
  │    2. Parse single-action JSON
  │    3. Execute that one action
  │    4. Repeat until action == "done"
  │
  └─→ Each iteration runs ONE of:
          • Task tool (subagent)
          • Task tool × N (parallel subagents)
          • Bash (deterministic script)
          • Surface ask_user payload to user, await response
          • Re-invoke next_action with --user-input
          • Stream final-report.md and stop

The state-driver decides each iteration based on disk state.
The LLM never tracks state. The LLM is the dispatcher.
```

Typical sequence (single matrix, 4 principles, no fatal severity, no loop) is identical to v5 §7. Multi-matrix flow shown in Appendix A.

---

## 8. Slash Commands

Unchanged from v5 except: `/triz-workshop:triz-list-matrices` filters by `meta.status` (and now respects `shell` status by default — shell matrices are listed but flagged "no cell data"). Full bodies in v5 §8.

---

## 9. Subagents

Each subagent is `agents/<name>.md` with YAML frontmatter and a system prompt body. Frontmatter fields used:

- `name` — subagent identifier
- `description` — natural-language description used by the orchestrator to decide when to invoke
- `tools` — restricted tool list
- `model` — `sonnet` for all
- `skills` — explicitly listed; **subagents do not inherit skills from the parent**, so each subagent that needs methodology background lists `triz-methodology`

Subagents return their work via the **final-message convention**: write the artifact to disk, return a brief summary string. The state-driver reads the artifact from disk; it doesn't try to parse the subagent's chat output.

The seven subagents and their schema-bound jobs are unchanged from v5 (§9.1–§9.7), except for two clarifications introduced in v6:

### 9.3a — Mapper alternatives are full pairs

The mapper's `alternatives` field is an array of full `(improving_param_id, worsening_param_id)` pairs, not single-axis substitutions. Lookup tries each full pair in order. This eliminates the "is the alternative for the improving or the worsening axis" ambiguity from v5.

```json
"alternatives": [
  {"improving_param_id": "9", "worsening_param_id": "37", "alt_strength": "medium"},
  {"improving_param_id": "39", "worsening_param_id": "37", "alt_strength": "medium"}
]
```

### 9.5a — Per-matrix interpreter prompt variants ship in Phase 2

The interpreter prompt branches on `matrix.meta.principle_taxonomy` and `matrix.meta.interpretation_lineage`:

| Lineage | Prompt addendum |
|---|---|
| `altshuller-40` | Standard. Apply principle to the user's domain. |
| `biotriz-40` | **Draw biological analogies explicitly.** Cite a biological mechanism if the principle has one. |
| `drug-safety-reframed` | The principle has been reinterpreted for governance. Use the reinterpreted description from the matrix file, not the classical Altshuller meaning. |
| `triz-ai-extended` | The matrix is LLM-curated. Apply standard principle meaning but note `interpretation_caveat: "matrix is LLM-generated; cross-validate against altshuller-40 if available"`. |

These variants are mandatory in Phase 2, not deferred to Phase 3. BioTRIZ's value-add is the biological analogies; shipping a generic interpreter for BioTRIZ misrepresents the matrix.

### 9.6a — Synthesizer dedup policy (v6 reset)

The v5 design said: "Use `canonical_id` to dedup principles across matrices (Altshuller's Segmentation and TRIZ-AI's Segmentation are one principle, not two)." This is **only correct at the principle-list layer** (don't list `P1 Segmentation` twice in the candidate's `principles_applied`). At the interpretation layer, two interpretations from different `interpretation_lineage`s are kept distinct.

Concrete example: a multi-matrix run selects `altshuller_39x39` and `biotriz_6x6_bio`. Both yield principle 1 (Segmentation). The interpreter produces two interpretations:

- `altshuller-40` lineage: "Split the fraud rule pipeline into mandatory-blocking (sync) and async-monitoring tiers."
- `biotriz-40` lineage: "Like cellular compartmentalization, segregate by access frequency — hot rules in ribosome-equivalent fast pathways, cold rules in nuclear-equivalent rare pathways."

Both go into the synthesizer. The synthesizer can combine, contrast, or pick. It does **not** discard either as redundant. The candidate's `principles_applied` lists `P_SEGMENTATION` once (with both interpretation refs); the candidate's `implementation_sketch` may draw on either or both.

This is amendment 3's "dedup at list, distinct at angle" policy.

---

## 10. Deterministic Scripts

Seven scripts, each invoked from the orchestrator via Bash. Unchanged from v5 except:

### 10.2a — `select_matrix.py` Stage A additions

In addition to v5's Stage A drops, drop matrices where:

- `meta.dimensions.populated_cells == 0` AND user did not explicitly specify via `--matrix=<id>`. (Handles Mann 2003 shell.)
- `meta.language` does not intersect `["en"]`. (Handles bilingual-only matrices in v0.1; reserved for revision when `--lang=` ships.)
- The matrix file fails to load or fails registry signature check.

### 10.3a — `lookup_principles.py` honors heterogeneity flags

- `meta.diagonal_cells == "included"`: matrix may be queried at i==j (BioTRIZ).
- `meta.diagonal_cells == "excluded"` AND mapper produced i==j: lookup returns `populated: false` immediately; state-driver branches to no-clean-mapping.
- `meta.parameter_id_style == "prefixed"`: lookup accepts string keys verbatim. (Handles `S1`/`T19` in healthcare_servqual.)
- If `populated == false`, lookup tries each `alternatives[]` pair in order before giving up.

---

## 11. The Methodology Skill

Unchanged from v5 §11. Skill body now mentions amendment 4 (language tag) and the `interpretation_lineage` taxonomy under "When the matrix is the wrong tool."

---

## 12. Validation Hooks

Unchanged from v5 §12.

---

## 13. Artifact Schemas

| File | Stage | Required fields |
|---|---|---|
| `01_problem.schema.json` | Problem framing | improving_concept, worsening_concept, domain_signals, contradiction_type, domain_class, framing_confidence |
| `02_selection.schema.json` | Matrix selection | weights_version, selected_matrices (≥1), run_strategy, stage_e_invoked |
| `03_mapping.schema.json` | Parameter mapping (mapper) | matrix_id, improving_param_id, worsening_param_id, **alternatives (array of pairs)**, mapping_confidence |
| `03c_independent_mapping.schema.json` | Mapping critic Phase 1 | matrix_id, improving_param_id, worsening_param_id, confidence, no_clean_mapping |
| `03b_mapping_critique.schema.json` | Mapping critic Phase 2 (deliberation; conditional) | matrix_id, verdict, chosen_mapping |
| `04_principles.schema.json` | Cell lookup | matrix_id, populated (bool), principles, alternatives_tried (array; for replay reproducibility) |
| `05_interpretation_single.schema.json` | One principle's interpretation (per-principle artifact) | matrix_id, principle_id, principle_canonical_id, **interpretation_lineage**, principle_name, concrete_suggestion, applies_how |
| `05_interpretations.schema.json` | Merged interpretations | interpretations (array; sorted by `(canonical_id, interpretation_lineage)`) |
| `06_solutions.schema.json` | Solution synthesis | candidates (1–4, named, with **principles_applied** [canonical_ids; deduped] AND **interpretation_refs** [array; not deduped]) |
| `07_critique.schema.json` | Solution critique | per_solution_critiques (with secondary_contradictions and severity) |
| `selector_tags_vocabulary.json` | Controlled vocab | the canonical list of allowed selector tags (amendment 2) |

Each schema carries a `schema_version` integer field. The plugin's `plugin.json:supported_artifact_schema_versions` lists which versions it can replay.

**Submatrix policy.** Each `matrix_id` corresponds to exactly one cell table. BioTRIZ ships as two ids: `biotriz_6x6_bio` and `biotriz_6x6_tech`. The submatrix-as-key convention from the v5 era is forbidden (storage design §5a).

---

## 14. Matrix Selection Algorithm

Implemented in `select_matrix.py` (Stages A–D) plus optional `triz-matrix-selector` subagent (Stage E).

### 14.1 The five stages

```
Stage A — Hard exclude (deterministic, in script)
  Drop matrices where ANY of:
    matrix.status ∈ {"identical-duplicate", "shell"} AND no --matrix= override
    matrix.dimensions.populated_cells == 0 AND no --matrix= override
    matrix.language does not intersect supported_languages   (v0.1: ["en"])
    problem.domain_signals ∩ matrix.selector_tags.excludes ≠ ∅
    matrix file fails to load or fails registry hash check

Stage B — Status floor (deterministic, in script)
  Drop matrices where:
    matrix.status == "experimental" AND framing_confidence == "high"
  (Rationale: when framing is uncertain, allow experimental matrices to surface;
   when framing is certain, prefer canonical/curated.)

Stage C — Redirect resolution (deterministic with cycle detection, in script)
  visited = set()
  For each remaining matrix M, depth ≤ 3:
    For each redirect entry in M.use_cases.skip_in_favor_of:
      target = entry.target_matrix_id
      if target ∈ visited: skip (cycle); log
      if target was Stage-A excluded: skip; log
      if entry.if_condition (DSL, amendment 1) matches problem signals:
        replace M with target; visited += {M, target}

Stage D — Score (deterministic, weights_version-tagged)
  For each remaining matrix M:
    domain_overlap   = |problem.domain_signals ∩ M.selector_tags.domains| × W1
    class_match      = problem.contradiction_type ∈ M.selector_tags.classes ? W2 : 0
    status_bonus     = LOOKUP(M.status, status_weights)
    exotic_match     = |problem.exotic_signals ∩ M.selector_tags.tags| × W4
    score(M) = sum

  v0 weights: W1=10, W2=20, W4=8;
              status_weights = {canonical: +5, domain: +15 if domain_class match,
                                variant: -2, derived: -3}.
  (W3/coverage_bonus removed in v6 — coverage is enforced as a Stage A floor instead.)
  Tagged "v0-uncalibrated" until eval-driven calibration ships.

  After scoring, set run_strategy:
    if 1 selected:                                run_strategy = "single"
    if ≥2 selected and parameter_taxonomy values all distinct:
                                                  run_strategy = "parallel"
    else:                                         run_strategy = "single"
                                                    (Stage E may override)

Stage E — LLM tiebreak (subagent dispatch via state-driver)
  if (top score − second score) / top < 0.15:
    set stage_e_invoked: true
    state-driver dispatches triz-matrix-selector subagent
  Stage E may also override run_strategy.
```

### 14.2 The `if` DSL

Defined in storage design amendment 1. Predicates: `exotic_signal`, `domain_signal`, `contradiction_type_is`, `domain_class_is`, `language_is`, `populated_cells_at_least`. Combinators: `any_of`, `all_of`, `not`. Free-text `if` is rejected at registry-validation time.

**Extension procedure** (amendment 1): adding a predicate requires a parser-case PR + unit test, a `registry.json:schema_version` minor bump, and the plugin's `compatibility.matrix_collection_schema` range update. Old plugins reject unknown predicates explicitly rather than silently ignoring them.

### 14.3 Cross-matrix principle dedup (corrected policy)

`principles[<id>].canonical_id` (amendment 3) is required on every matrix file. Two principles with the same `canonical_id` across matrices share a list-level identity but **not** an interpretation-level identity:

- **List-level dedup (apply):** `06_solutions.json:candidates[].principles_applied` is a deduped array of canonical ids. Don't list "P_SEGMENTATION" twice because two matrices both invoked it.
- **Interpretation-level distinctness (preserve):** `05_interpretation_*.json` artifacts are written per `(matrix_id, principle_id)` and merged into `05_interpretations.json` without dedup. The synthesizer reads all interpretations and may combine, contrast, or pick — never silently drop.

The candidate's `interpretation_refs` array carries pointers to every interpretation that contributed, including multiple from the same `canonical_id` when their `interpretation_lineage` differs. Reports show this.

### 14.4 Categorical confidence everywhere

Same as v5: high / medium / low for `framing_confidence`, `selection_confidence`, `mapping_confidence`. No scalar confidence anywhere in the system.

### 14.5 Calibration plan

Once the eval set has ≥30 labeled cases, grid-search W1, W2, W4 and the status_weights table over the labeled set. Pick weights maximizing weighted F1 of (selection precision × no-clean-mapping recall × principle Jaccard). Bump `weights_version` from `v0` to `v1`. Old runs replay against `v0` by reading their manifest.

---

## 15. Two-Phase Mapping Critic

Unchanged from v5 §15.

The mechanical `compare_mappings()` function in v6 has one addition: when either mapper or critic declares the mapping is on a matrix with `meta.parameter_id_style == "prefixed"`, comparison is string-equality on the prefixed id, not numeric coercion.

---

## 16. No-Clean-Mapping Branch

Per goal 7, the pipeline treats unmappable problems as a normal output, not an error. Three triggers from §15.3:

1. Phase 1 critic returns `no_clean_mapping_likely: true`.
2. Lookup returns empty cell *and* all mapper alternatives also return empty cells.
3. Either mapper or critic returns `confidence: low`.

When triggered, the state-driver:

1. Skips lookup, interpretation, synthesis, contradiction-critic stages.
2. Emits `run_script` for `assemble_report.py` with `--no_resolution` flag.
3. The report includes:
   - The structured problem.
   - The closest two parameter pairs the mapper considered (with rationales) and the critic's independent attempt.
   - **Neighborhood-suggestive principles**, defined explicitly (v6): for each candidate parameter pair, list principles from cells that share a parameter group with the mapper's pair. Parameter groups for `altshuller-39` are the seven blocks identified in `meta_analysis.md` (physical_geometry_1_8, mechanical_9_14, temporal_durability_15_16, energy_thermal_17_22, loss_quantity_23_26, quality_system_27_31, usability_manufacturing_32_39). For other matrices, the matrix file may declare `meta.parameter_groups`; if absent, this section is omitted with a note. Labeled "not a direct lookup; suggestive only."
   - A note: this contradiction is not standardly resolved by the matrix; consider reformulation, ARIZ, or a different methodology.

Failing here is a feature, not a bug.

---

## 17. Fatal-Severity Flow

`triz-contradiction-critic` returns a critique with `severity: "fatal"` on at least one candidate.

### 17.1 The scenario

A fatal critique is something like: "Candidate B (pre-computed risk envelope) introduces a regulatory issue — pre-computing risk scores from PII without consent likely violates GDPR Article 22. Pursuing this candidate without legal review would be reckless." Demands stop-and-rethink.

### 17.2 The flow

When `next_action.py` reaches stage `check_fatal_severity`, it reads `07_critique.json` and categorizes:

- `none_fatal`: nominal continuation
- `some_fatal`: at least one but not all fatal
- `all_fatal`: every candidate fatal

For `some_fatal` and `all_fatal`, the state-driver emits an `ask_user` action with structured options.

### 17.3 The decision payload

```json
{
  "kind": "fatal_severity_in_critique",
  "run_id": "...",
  "stage_paused_at": "07_critique",
  "fatal_candidates": [...],
  "non_fatal_candidates": [...],
  "options": [
    { "id": "drop_fatal_proceed", "label": "Drop the fatal candidate(s); proceed with the others.", "available_when": "some_fatal" },
    { "id": "reformulate_with_constraint", "label": "Add a constraint to the original problem and re-run synthesis.", "prompts_user_for": "constraint_text" },
    { "id": "try_different_matrix", "label": "Re-run with a different matrix (override auto-selection).", "prompts_user_for": "matrix_id" },
    { "id": "accept_with_override", "label": "Accept the fatal candidate anyway (logged as explicit override)." },
    { "id": "abandon_with_writeup", "label": "Abandon the run; produce a 'no acceptable resolution' report." }
  ]
}
```

`abandon_with_writeup` is now available on **both** `some_fatal` and `all_fatal` (v5 restricted it to all_fatal — v6 corrects this since a fatal critique can reframe the entire problem).

### 17.4 What each option does

| User choice | State-driver action |
|---|---|
| `drop_fatal_proceed` | Mark fatal candidates excluded; advance to assembly with surviving candidates only |
| `reformulate_with_constraint` | Append constraint to `01_problem.json:constraints`; reset state to framer; re-run from synthesis |
| `try_different_matrix` | Append `--matrix=<id>` flag; reset state to selection; re-run from mapping |
| `accept_with_override` | Mark `override_logged: true` in manifest; advance to assembly |
| `abandon_with_writeup` | Set state to assembly with `--no_resolution` |

### 17.5 Universality

Same `ask_user` mechanism handles framing-clarification, mapping-disagreement, validation-failure, retry-cap-reached, and fatal-severity. One pause/resume primitive, many use cases.

---

## 18. Run Artifacts, Replay, Manifest

Layout (§18.1), manifest (§18.2), and state.json (§18.3) are unchanged from v5 except: manifest now carries `matrix_collection_schema_version` matching the registry's amendment level (1.1 minimum for v0.1).

### 18.4 Replay semantics (v6 update)

`/triz-workshop:triz-replay <run-id>`:

1. Read `manifest.json`. Check `artifact_schema_version` is in the current plugin's `supported_artifact_schema_versions`.
2. With no flags: re-run the entire pipeline with the same problem and the same registry snapshot (from cache).
3. `--from=<stage>`: invalidate artifacts ≥ that stage; re-run from there.
4. `--rerun-only=<stage>`: invalidate artifacts > that stage (cascade rule); re-run that stage only, then re-run downstream.
5. `--use-current-registry`: ignore cached snapshot; use whatever's at `${TRIZ_MATRICES_PATH}` now.

**Stale-registry semantics (v6 addition):** if `--use-current-registry` is set and a matrix that the original run referenced has been renamed, deleted, or has a non-matching content hash, the state-driver emits an `ask_user` action with options:

- `migrate_to_new_id` (when rename detected via `meta.lineage.supersedes`): rewrite artifact references and continue.
- `abort_replay`: stop with an explanation.
- `proceed_with_snapshot`: ignore `--use-current-registry` and use the cached snapshot instead.

No silent fallback. A replay against a moved matrix never produces results that look correct but reference the wrong corpus.

Cascade rule: invalidating stage N invalidates all stages > N.

---

## 19. Argparse Hardening & Retry Counters

Unchanged from v5 §19.

---

## 20. Testing Strategy

Unchanged structure from v5 §20 (5 layers, 50 fixtures, 90% coverage gate). Two additions in v6:

### 20.11 Layer 6 — Real-registry integration test

A single test that loads the *actual* `${TRIZ_MATRICES_PATH}/registry.json` and asserts:

- Every `matrix_file` path resolves and parses as JSON.
- Every parsed file conforms to the storage-design schema (with amendment 5).
- Every `matrix_id` referenced in any `skip_in_favor_of` resolves.
- Every `selector_tags.*` value is in `selector_tags_vocabulary.json` (amendment 2).
- Every `principles[].canonical_id` is non-empty (amendment 3).
- Every `meta.language` is a valid BCP 47 tag (amendment 4).

This catches the failure mode where fixtures are clean but reality has drifted. Runs in CI on every PR; runs locally as a pre-commit option.

### 20.12 Layer 7 — Heterogeneity-handling tests

Targeted integration tests using the corpus's known edge cases:

- `test_mann_shell_matrix_dropped_at_stage_a`
- `test_biotriz_bio_and_tech_are_distinct_ids`
- `test_healthcare_prefixed_ids_round_trip`
- `test_drug_safety_principle_lineage_routed_to_governance_prompt`
- `test_innovatetriz_bilingual_filtered_when_lang_not_supported`

These exist independently of the 50 fixture-based state tests so corpus changes can't quietly disable them.

---

## 21. Eval Harness

Unchanged structure from v5 §21. Three additions in v6:

### 21.3a Additional metrics

- **Shared-blind-spot rate.** Of cases where mapper and Phase 1 critic agree, what fraction are wrong against human consensus? This measures the residual risk of same-model-family agreement (v5 risk #3).
- **Cross-matrix angle preservation.** When a multi-matrix run produces interpretations from different `interpretation_lineage`s, does the final report present them as distinct angles (good) or collapse them (regression)?
- **Heterogeneity routing accuracy.** For BioTRIZ-eligible cases, is `biotriz_6x6_bio` selected (vs. accidentally landing on `biotriz_6x6_tech`)? For governance cases, does drug_safety win? Etc.

---

## 22. Failure Modes & Recovery

| Failure | Detection | Response |
|---|---|---|
| Compatibility check fails | `compatibility_check.py` exit code | Halt with actionable error before any pipeline work |
| Argparse error in `next_action.py` | Internal try/except | Emits `self_correct` action |
| Internal exception in `next_action.py` | Top-level try/except | Emits `self_correct` or `ask_user` (state_corrupted) |
| Framer confidence "low" | Categorical output | `ask_user` with clarify_framing options |
| Selector returns 0 matches | Empty `selected_matrices` | `ask_user` with closest candidates |
| All candidate matrices are shell | Stage A drops them all | `ask_user` to confirm `--matrix=<id>` override or abandon |
| Mapping critic Phase 1 says `no_clean_mapping=true` | Critic verdict | Branch to no-clean-mapping output |
| Mappings disagree | Mechanical comparison | Phase 2 deliberation dispatch |
| Mapper invalid param ID for matrix's `parameter_id_style` | State-driver pre-dispatch check | Re-dispatch once; if fails, halt |
| Mapper produces i==j on diagonal-excluded matrix | State-driver post-mapping check | Branch to no-clean-mapping |
| Lookup empty cell | Script returns `populated: false` | Try alternatives; if all empty, no-clean-mapping branch |
| Synthesizer 0 candidates | Schema requires ≥1 | Re-dispatch; if fails, return interpretations as raw |
| Critic finds `severity: "fatal"` | Schema | `ask_user` with fatal-severity options (incl. abandon_with_writeup) |
| Loop depth exceeds cap | State counter | Stop loop, return last good solution |
| Concurrent run-id collision | UUID4 suffix | Cannot occur by construction |
| Hook command fails | Hook exit code | Logged to `.triz/hook.log`; state-driver's pre-dispatch check is the contract |
| Subagent didn't write expected artifact | State-driver checks `expected_artifact` | `ask_user` with retry/abort/skip options |
| **Matrix file missing/unreadable mid-run** | State-driver pre-dispatch check before mapping each selected matrix | `ask_user` with: drop this matrix and continue, abort, retry-load |
| **Replay finds renamed/deleted matrix** | `--use-current-registry` + missing id | `ask_user`: migrate (if lineage permits), abort, or use snapshot |
| Stage retried 3× without success | Per-stage retry counter | `ask_user` without retry option |
| LLM dispatches wrong subagent (drift) | Next consultation sees unexpected/missing artifact | Re-emits same action; if happens twice, escalates to `ask_user` |
| State.json corrupted | `next_action.py` validation fails | `ask_user` with state_corrupted, options abort or attempt_repair |

---

## 23. Configuration Surface

Three layers, in precedence order:

**Layer 1 — Slash-command flags** (highest precedence). Per-invocation: `--matrix=`, `--matrices=`, `--auto-loop`, `--max-loops=N`, `--no-critique`, `--no-mapping-critic`. Parsed by `next_action.py` from `--user-prompt` on `--new-run`.

(`--lang=` is reserved for v1.0+ and not implemented in v0.1. v0.1 supports English only and filters non-English-only matrices at Stage A.)

**Layer 2 — Project config: `.triz/config.json`.** Project-local, version-controlled.

```json
{
  "matrices_path": "../shared-triz-matrices",
  "default_flags": { "max_loops": 2, "auto_loop": false },
  "weights_profile": "v1-software"
}
```

**Layer 3 — Environment variables** (lowest precedence).
- `TRIZ_MATRICES_PATH` — default `./Triz_matrixes`
- `TRIZ_WORKSHOP_LOG_LEVEL` — default `info`
- `TRIZ_WORKSHOP_CACHE_DIR` — default `.triz/cache`

Precedence: flag > project config > env var > built-in default.

---

## 24. Three-Axis Versioning

Unchanged from v5. Note: `compatibility.matrix_collection_schema: ">=1.1.0 <2.0.0"` (was `>=1.0.0` in v5; v0.1 of the plugin requires storage design v1.1's amendments to be live).

---

## 25. Plugin Layout & Distribution

Unchanged from v5 §25.

---

## 26. Phasing

**Phase 0 — Storage prerequisites (BLOCKING MILESTONE, not a checklist).**

This phase must complete before *any* Phase 1 work begins. The plugin's design depends on amendments 1–5 of `matrix_storage_design.md` being live in real matrix files, not just specified.

Concrete deliverables:

1. Every matrix file has structured `meta` per amendment 5: `id`, `status`, `dimensions {rows, cols, populated_cells}`, `lineage {derived_from, supersedes, identical_to}`, `language`, `parameter_id_style`, `diagonal_cells`, `principle_taxonomy`, `interpretation_lineage`.
2. `registry.json` exists with `schema_version: 1.1`, an entry per matrix id.
3. `selector_tags_vocabulary.json` exists; every `selector_tags.*` value in every use-case file draws from it.
4. Every principle in every matrix has `canonical_id` (amendment 3) and `interpretation_lineage`.
5. Every `skip_in_favor_of[].if` is in DSL form (amendment 1).
6. BioTRIZ is split into `biotriz_6x6_bio` and `biotriz_6x6_tech` files with distinct ids.
7. `validate_artifact.py` (in registry-validation mode) passes against the live corpus.

**Estimate.** Hand-classification of ~1500 principle entries across ~10 matrices for `canonical_id` is the bulk. Realistic cost is 2–3 weeks of focused work, not "Phase 0 prep." This is the dominant schedule risk and surfaces here as such.

**Phase 1 — Skeleton + state-driver + eval/test scaffolding.** Same as v5 Phase 1. Adds layer-6 real-registry integration test and layer-7 heterogeneity tests.

**Phase 2 — Real subagents (incl. mapping critic Phase 1, BioTRIZ prompt variant).** Per-matrix interpreter prompt variants (§9.5a) ship in this phase, not Phase 3.

**Phase 3 — Synthesis & critique + remaining test fixtures.** Same as v5 Phase 3. v0 → v1 weight calibration.

**Phase 4 — Multi-matrix, loops.** Russian-language path moved to Phase 5+ (was Phase 4 in v5).

**Phase 5 — Polish & marketplace publication.** Same as v5.

**Phase 5+/v1.0 — Multilingual.** `--lang=` flag, non-English subagent prompts, bilingual matrix support beyond English filtering.

---

## 27. Open Questions & Acknowledged Risks

### 27.1 Open questions

1. **Methodology skill as a sibling plugin?** Defer until a second consumer exists.
2. **First-run UX without a matrix collection.** Halt-with-error acceptable for v0.1.
3. **Telemetry.** Default OFF; opt-in later.
4. **Global retry budget.** Per-stage caps prevent loops within a stage; cross-stage cap deferred.
5. **Property test strategy generators.** Defer to Phase 3 if Phase 1 fixtures + units catch enough bugs.
6. **CI cost.** Nightly comprehensive + fast PR-time subset.

(Closed in v6: per-matrix interpreter prompt variants — promoted to Phase 2.)

### 27.2 Acknowledged risks

1. **The methodology itself is contested.** Souchkov reports ~10–15% clean-mapping rate. README will say so.
2. **`triz_ai_50x50` is itself LLM-output.** Compounding-error risk; the `interpretation_lineage: "triz-ai-extended"` flag adds an explicit caveat in interpreter output. Eval set should include cases where this matrix is selected and human-validated principles diverge.
3. **Mapper and Phase 1 critic share a model family.** Independence is partial. Layer-6 eval metric "shared-blind-spot rate" measures this over time.
4. **Selection weights are uncalibrated until v1.** `weights_version` audit trail.
5. **State-driver complexity.** 90% coverage gate.
6. **Latency overhead.** ~21s on small runs, ~30s on multi-matrix runs (~60% overhead). See §6.7.
7. **Phase 0 size.** Hand-classification of `canonical_id` and `selector_tags` is 2–3 weeks of focused work. The plugin cannot ship without it.
8. **Heterogeneity declarations may drift from reality.** A matrix author marking `diagonal_cells: "excluded"` while populating diagonal cells silently produces wrong results. Layer-6 integration test (§20.11) checks this.

---

## 28. Why This Design Looks Like This

(v5 entries kept; v6 additions appended.)

**Why a Python state-driver and not LLM orchestration.** Match the tool to the task: small atomic jobs to LLMs, state machines to code.

**Why state-driver and not full inversion via SDK.** Keeps the LLM as the dispatcher within Claude Code's primitives without adding a hard SDK dependency.

**Why one action per call, not a batch.** Atomic transitions are recoverable from disk state.

**Why 7 subagents instead of 1 god-tier solver.** Specialists with one schema each materially improve output.

**Why structural blinding for the mapping critic, not procedural.** LLMs cannot un-see what's in their context.

**Why the orchestrator is the slash command, not a subagent.** Avoids fictional uniformity.

**Why deterministic scripts in-process, not as subagents.** Uniformity is at the artifact layer (every step writes a 0N_*.json), not the invocation shape.

**Why `skip_in_favor_of` is honored before scoring.** Hand-curated routing wisdom beats general-purpose scoring.

**Why per-stage artifacts on disk, not chat-channel handoff.** Replay, audit, isolated subagent contexts.

**Why a hook AND state-driver validation.** PostToolUse can prompt feedback but cannot undo writes. Belt and suspenders with clear responsibilities.

**Why the mapping critic is not optional.** Souchkov's empirical finding makes parameter mapping a 10–15%-success operation when done by experts.

**Why categorical confidence everywhere.** LLM-produced 0.0–1.0 values aren't well-calibrated; thresholding is false precision.

**Why `ask_user` is a first-class action type.** Pause/resume needs to be designed, not bolted on.

**Why state on disk, not in process memory.** No daemon, no session, no in-memory orchestrator.

**Why three version axes.** Plugin code, matrix collection, and artifact schemas evolve at different rates.

**Why 90% coverage on `next_action.py`.** The state-driver IS the system now.

**Why test fixtures are filesystems, not Python objects.** Adding a test case is creating a directory with five small JSON files.

**v6 additions:**

**Why the matrix corpus is heterogeneous by declaration, not by inference.** Filename heuristics ("if name contains 'biotriz', use biological prompts") are brittle and silent — a renamed file produces wrong results with no warning. Declaring `meta.principle_taxonomy`, `meta.diagonal_cells`, `meta.parameter_id_style`, `meta.interpretation_lineage` makes per-matrix conventions explicit, machine-checkable, and reviewable. Code branches on declarations. New matrices declare their conventions; old code keeps working.

**Why `canonical_id` dedups principle lists but not interpretations.** Multi-matrix triangulation is valuable specifically because two matrices encode different perspectives on the same principle. BioTRIZ's "Segmentation as cellular compartmentalization" and Altshuller's "Segmentation as physical splitting" are *not the same insight*. Collapsing them at the synthesizer eats the value of running both matrices. The list-level dedup is real (don't claim "P1 + P1" in `principles_applied`); the interpretation-level distinctness is the point. v5 conflated these layers; v6 separates them.

**Why Phase 0 is a blocking milestone, not a checklist item.** The plugin design assumes amendments 1–5 are live in real matrix files. Until `canonical_id`, `selector_tags`, structured `if`-DSL, `meta.language`, and structured `meta.dimensions` exist in the corpus, every downstream component is building on fiction. Hand-classifying ~1500 principles for `canonical_id` is a real 2–3 week investment. Pretending it's prep underprices the work and causes Phase 1 to land in a corpus that won't support it.

**Why coverage_bonus was removed from Stage D scoring.** Density correlates with breadth, not relevance. Heinrich's curated 109-cell matrix may be exactly right for a problem but score lower than Altshuller's 1244-cell matrix on absolute density. v5's `log10(populated_cells + 1) × W3` rewarded the wrong direction. v6 enforces coverage as a Stage A floor (`populated_cells == 0` → drop) and otherwise treats coverage as neutral; status weights and selector_tags overlap carry the relevance signal.

**Why submatrix split, not submatrix-as-key.** BioTRIZ shipping as a single file with `matrix` and `matrix_technology` keys forces every downstream component to special-case the file shape. Splitting into `biotriz_6x6_bio` and `biotriz_6x6_tech` is a one-time corpus change that eliminates a permanent special case in mapper, lookup, interpreter, and synthesizer code. The cost is one extra registry entry; the saving is no per-stage submatrix-key handling.

**Why `--lang=` is deferred.** Bilingual matrices and non-English subagent prompts are a feature, not v0.1 scope. Filtering non-English-only matrices at Stage A is correct for v0.1 (no false-language results); building real multilingual support is v1.0 work. Removing the half-implemented `--lang=` flag from v5's §23 is honest.

---

## Appendix A — Sample Run

(Unchanged single-matrix flow from v5. Two-matrix triangulation flow showing v6's distinct-angle preservation:)

User: `/triz-workshop:triz-solve "We need flexible policy enforcement that survives partial system failures, like a biological organism survives single-cell death."`

After framer: `domain_signals: ["software", "resilience"]`; `exotic_signals: ["bio-analogy"]`. Stage D selects `triz_ai_50x50` (score 78) and `biotriz_6x6_bio` (score 71). Both within 15%; Stage E confirms parallel run (different parameter taxonomies). Mappers + Phase-1 critics fire in parallel × 2 matrices = 4 subagent calls. Both matrix mappings agree internally. Lookup yields P1 (Segmentation) + P15 (Dynamics) on `triz_ai_50x50`; P1 (Segmentation) + P3 (Local quality) on `biotriz_6x6_bio`. Interpreter fires per (matrix, principle) = 4 calls. The two P1 interpretations have distinct `interpretation_lineage` values (`triz-ai-extended` vs `biotriz-40`); both are preserved in `05_interpretations.json`. Synthesizer produces 3 candidates, each with `principles_applied: ["P_SEGMENTATION", "P_DYNAMICS"]` (deduped) and `interpretation_refs: [...]` (3 distinct interpretations referenced). Final report presents the engineering and biological framings as separate paragraphs under each candidate, not as a single deduplicated bullet.

---

## Appendix B — What the LLM's Chat Context Actually Looks Like

Unchanged from v5.

---

## Appendix C — Sample Test Fixture

Unchanged from v5.

---

## Appendix D — Component Cross-Reference

Unchanged from v5.

---

## Appendix E — v5→v6 Changelog

This appendix lists every substantive change from v5 to v6 so reviewers can audit the delta.

**Goals.** Added goal #10 (heterogeneity is first-class). Tightened goal #3 ("triangulation that preserves angle").

**Architectural principles.** Added #13 (heterogeneity declared, not inferred) and #14 (cross-matrix angles stay distinct).

**§9.3a (new).** Mapper alternatives are full pairs, not single-axis substitutions. Closes a v5 schema ambiguity.

**§9.5a (new).** Per-matrix interpreter prompt variants ship in Phase 2 (was Phase 3 in v5). BioTRIZ value-add was misrepresented otherwise.

**§9.6a (new).** Synthesizer dedup policy: list-level dedup applies; interpretation-level distinctness preserved. v5 conflated these layers.

**§10.2a (new).** `select_matrix.py` Stage A additions: drop shell matrices, language-mismatched matrices, unloadable matrices.

**§10.3a (new).** `lookup_principles.py` honors `meta.diagonal_cells` and `meta.parameter_id_style`.

**§13.** Schema: `03_mapping` requires `alternatives` as full pairs. `05_interpretation_single` adds `interpretation_lineage`. `06_solutions` separates `principles_applied` (deduped) from `interpretation_refs` (not deduped). Submatrix policy explicit: one `matrix_id` per cell table.

**§14.1.** Stage A enriched (shell drops, language drops, file-load drops). Stage D loses `coverage_bonus` (W3 removed). Stage D explicitly sets `run_strategy`. Comment explaining experimental-gate behavior added.

**§14.2.** `if`-DSL extension procedure documented.

**§14.3.** `canonical_id` dedup policy rewritten to "list-level only; interpretations stay distinct."

**§16.** "Closest neighboring populated cells" defined semantically (parameter groups from `meta_analysis.md`); declarable per matrix via `meta.parameter_groups`.

**§17.3.** `abandon_with_writeup` available on `some_fatal` too.

**§18.4.** Stale-registry replay handling added: `migrate_to_new_id` / `abort_replay` / `proceed_with_snapshot`.

**§20.11 (new).** Layer-6 real-registry integration test.

**§20.12 (new).** Layer-7 heterogeneity tests.

**§21.3a (new).** Eval metrics for shared-blind-spot rate, cross-matrix angle preservation, heterogeneity routing accuracy.

**§22.** Failure-modes table adds: matrix file missing/unreadable mid-run; replay finds renamed/deleted matrix; mapper produces i==j on diagonal-excluded matrix; mapper invalid id for `parameter_id_style`; all-shell selection result.

**§23.** `--lang=` flag removed; v0.1 is English-only by Stage A filter. Documented explicitly.

**§24.** `compatibility.matrix_collection_schema` floor raised to `>=1.1.0`.

**§26.** Phase 0 reframed as blocking milestone with concrete deliverables and an honest 2–3 week estimate. Per-matrix prompt variants moved Phase 3 → Phase 2. Russian-language path pushed to Phase 5+/v1.0.

**§27.1.** Per-matrix interpreter prompt variants closed (promoted to Phase 2).

**§27.2.** Added risks: Phase 0 size; heterogeneity-declaration drift.

**§28.** Added explanations for: heterogeneity by declaration; canonical_id-dedups-lists-not-interpretations; Phase 0 is blocking; coverage_bonus removal; submatrix split; `--lang=` deferred.

**Storage design dependency.** v5 referenced "amendments 3 and 4" inline; v6 references storage design v1.1 amendments 1–5 (DSL, controlled vocab, canonical_id, language, structured dimensions) plus heterogeneity rules in storage design §5a (one submatrix per file, parameter_id_style, diagonal_cells, principle_taxonomy, shell-status flag).
