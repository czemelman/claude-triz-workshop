# Changelog

All notable changes to `prizm` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-05-13

### Added

- **`digest.html` — a self-contained dark-theme HTML report** emitted by
  `assemble_report.py` alongside `final-report.md` at the end of every
  `/prizm:solve` run. Stat cards (matrices / principles / candidates /
  severity counts), pipeline strip, contradiction pole layout,
  matrix-selection cards, Phase 2 verdict pills, severity-color-coded
  candidate cards, collapsible drill-downs for implementation sketch /
  contributing interpretations / critique. Inline CSS, no JS, no external
  assets — opens cleanly from disk or via htmlpreview.github.io.
- **`generate_digest.py`** — standalone digest renderer. Reads the
  artifacts in `.triz/runs/<run-id>/` and produces `digest.html`. Can be
  re-run independently to regenerate or to render a digest for an
  externally-edited run.
- **README revamp.** Added Mermaid pipeline / two-phase-critic /
  architecture diagrams, concrete use-case examples per matrix lineage,
  a "when not to use this" section, and links to the sample digest +
  Markdown report under `docs/examples/`.
- **`docs/examples/`** — `digest-nfc-attestation.html` and
  `final-report-nfc-attestation.md` from a real end-to-end run on an
  NFC-chip + blockchain authentication architecture problem.

## [0.1.1] - 2026-05-13

Post-MVP refinements driven by the first full end-to-end production run
(NFC chip / continuity architecture brief). All fixes are additive and
back-compatible with 0.1.0 state files.

### Fixed

- **Schema validation now covers script-written artifacts.** Previously the
  `PostToolUse` hook only fired for subagent `Write`/`Edit` calls, leaving
  `02_selection.json`, `04_principles_*.json`, `05_interpretations.json`,
  and `final-report.md` without a write-time gate. `_common.atomic_write`
  now validates against the artifact's schema when one is known (controlled
  by a new `validate` keyword, default `True`).
- **`awaiting_decision.json` is removed once the user answers.** The
  sentinel previously persisted past the resolved decision, misleading
  replay tooling into thinking the run was still paused.
- **`state.selected_matrices` is resynced after Stage E.** The selector
  subagent could rewrite `02_selection.json` in Stage E, but
  `state.selected_matrices` retained the pre-Stage-E set. The
  `_stage_stage_e_check` handler now refreshes the cached list before
  advancing to mapping.
- **`select_matrix.py` no longer logs misleading counts when Stage E is
  invoked.** The Stage D `selected` count and `strategy` are provisional
  in that branch; the log now says `(stage_e_invoked=True, awaiting LLM
  tiebreak)` instead.
- **Slash-command dispatcher contract clarified.** `commands/solve.md`
  now states that `subagent_type` must be `prizm:<action.subagent>`
  (the previous wording said `subagent` literally, which is not a valid
  agent type). Resolves the "Agent type not found" error on the first
  framer dispatch of a fresh session.

### Added

- **Stable solution ids in the fatal-severity ask_user prompt.** The
  `fatal_severity_in_critique` action now carries `candidates_with_ids`
  pairing each candidate with an ordinal id (`s1`, `s2`, ...). The
  `drop_fatal_proceed` user-input payload accepts a new
  `fatal_solution_ids` field as the preferred selector; legacy
  `fatal_candidates` (free-text names) still works.
- **`assemble_report.py --exclude` accepts solution ids.** Either
  `--exclude "<candidate name>"` or `--exclude s2` drops a candidate.
- **`final-report.md` trace counts `partial/` artifacts.** The
  per-principle interpretation files that `merge_interpretations.py`
  moves into `partial/` are now enumerated under the Trace footer rather
  than vanishing from the count.

### Changed

- **`_common.atomic_write` chmods to 0644 after rename.** Script-written
  artifacts were previously `0600` (mkstemp default); subagent-written
  artifacts via the `Write` tool were `0644`. The split is now uniform.

## [0.1.0] - 2026-05-13

Initial Phase 1 release. Skeleton + state-driver + eval/test scaffolding per
design v6.
