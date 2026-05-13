# prizm

*(repository: `claude-triz-workshop`)*

A Claude Code plugin that turns a TRIZ contradiction-matrix collection into a working multi-agent inventive-problem-solving pipeline.

Given a problem statement, the plugin:
1. Frames it as a TRIZ contradiction (improving + worsening parameters).
2. Selects the best-fitting matrix from a corpus of nine (engineering, biology, healthcare, AI-extended, bilingual).
3. Maps the contradiction to that matrix's parameter taxonomy — with a structurally-blinded independent critic catching anchor bias.
4. Looks up the recommended inventive principles.
5. Expands each principle into a concrete domain-specific suggestion.
6. Synthesizes 2–4 candidate solutions, preserving cross-matrix angles.
7. Stress-tests each candidate for secondary contradictions and fatal-severity risks.

Every step writes an auditable JSON artifact. Runs are replayable.

## Layout

```
.
├── prizm/                            # the Claude Code plugin (THIS is what /plugin install grabs)
│   ├── .claude-plugin/plugin.json
│   ├── agents/                       # 7 LLM subagents
│   ├── commands/                     # 4 slash commands
│   ├── scripts/                      # 9 deterministic Python scripts (state-driver + selection + lookup + assembly)
│   ├── schemas/                      # 11 JSON Schemas (artifact contracts)
│   ├── skills/triz-methodology/      # TRIZ methodology skill
│   ├── tests/                        # 145 tests (unit + integration + property + e2e_replay)
│   ├── eval/                         # 30 labeled cases + synthetic eval harness
│   └── data/                         # bundled matrix corpus — ships with the plugin install
│       ├── matrices/                 # 9 bundled matrix files + redundant/ provenance copies
│       ├── use_cases/                # 11 v6-shaped use-case files (what each matrix is for)
│       ├── registry.json             # single index of all matrices (loaded by the plugin)
│       └── selector_tags_vocabulary.json
│
├── validate_matrix.py                # strict v6 validator (reads from prizm/data/)
├── scripts/                          # corpus-maintenance scripts (migrate, normalize, regenerate registry)
├── triz_workshop_design.md           # full plugin design (v6)
├── matrix_storage_design.md          # storage schema for the matrix corpus (v1.1)
├── meta_analysis.md                  # statistical analysis across matrices
├── redundancy_analysis.md            # which matrices are identical to which
├── LICENSES.md                       # per-matrix license matrix + attribution lines
└── MATRICES_OPTIONAL.md              # how to fetch the 2 non-bundled matrices
```

## Install

### Option 1 — Via Claude Code marketplace (recommended)

Inside Claude Code:

```
/plugin marketplace add czemelman/claude-triz-workshop
/plugin install prizm@prizm
/reload-plugins
```

That's it. The matrix corpus is bundled inside the plugin (`prizm/data/`) so no env var is required — `_common.py` finds it automatically.

### Option 2 — Local dev install (symlink)

```bash
git clone git@github.com:czemelman/claude-triz-workshop.git ~/dev/claude-triz-workshop
ln -s ~/dev/claude-triz-workshop/prizm ~/.claude/plugins/prizm
# Restart Claude Code so it picks up the new plugin manifest.
```

### Override the corpus location (optional)

If you maintain your own customized matrix corpus elsewhere, point the plugin at it:

```bash
export TRIZ_MATRICES_PATH=/path/to/your/corpus  # must contain registry.json
```

### Using it

```
/prizm:list       # see what's available
/prizm:explain altshuller_39x39
/prizm:solve "Reduce car body weight without losing crash safety."
```

## Bundled matrices

| Matrix | License | What it's for |
|---|---|---|
| `altshuller_39x39` | Public domain | Classic engineering (1244 cells, the canonical) |
| `altshuller_russian_original` | Public domain | Russian-language original of the canonical |
| `heinrich_39x39` | Apache-2.0 | Curated 109-cell subset for AI-driven inventive solving |
| `triz_ai_50x50` | MIT | LLM-curated 50-parameter extension (security, sustainability, scalability, etc.) |
| `biotriz_6x6_bio` | CC BY 4.0 | Biology-derived contradiction resolutions (biomimetics) |
| `biotriz_6x6_tech` | CC BY 4.0 | Technology-derived comparison submatrix |
| `biotriz_24x24` | CC BY 4.0 | Expanded BioTRIZ with supplementary similarity/NEP data |
| `healthcare_servqual` | CC BY 4.0 | Hybrid SERVQUAL × TRIZ for service quality problems |
| `innovatetriz_extended` | MIT | Bilingual (Chinese / English) extended matrix |

**Not bundled (license-restricted):** `drug_safety_18x18` (CC BY-NC-ND 4.0) and `mann_matrix2003_48x48` (used-with-permission). See `MATRICES_OPTIONAL.md` for how to add them yourself.

## License

The plugin code is **MIT**. The matrix corpus is a mosaic of independently-licensed sources; see `LICENSES.md` for the full breakdown and attribution lines.

## Design provenance

This plugin was built top-down from a written design (`triz_workshop_design.md` v6, six adversarial-review rounds) against a curated matrix corpus (`matrix_storage_design.md` v1.1, with formal amendments for the storage schema). The build was driven by a state-driver Python pattern (the state machine lives in code, the LLM is a one-shot dispatcher per turn) and validated by 145 tests with 82% line coverage on the core state-driver. Eval routes 30/30 labeled cases.

See the design docs for the why behind every architectural decision.
