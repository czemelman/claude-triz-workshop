# TRIZ Matrix Storage & Purpose Design

Date: 2026-05-04
Version: 1.1 (adds amendments §6 to support `triz-workshop` plugin).

This document consolidates the analysis of the current `Triz_matrixes/` folder and proposes a design for how matrices should be stored and how their purpose should be defined.

---

## 1. Current State

### 1.1 Folder layout

```
Triz_matrixes/
├── matrices/
│   ├── altshuller_39x39.json
│   ├── altshuller_russian_original.json
│   ├── biotriz_6x6.json
│   ├── biotriz_24x24.json
│   ├── drug_safety_18x18.json
│   ├── healthcare_servqual.json
│   ├── heinrich_39x39.json
│   ├── innovatetriz_extended.json
│   ├── mann_matrix2003_48x48.json
│   ├── triz_ai_50x50.json
│   └── redundant/
│       ├── matriz_org_39x39.json
│       └── triz_agents_39x39.json
├── use_cases/
│   ├── altshuller_39x39_use_cases.json
│   ├── altshuller_russian_use_cases.json
│   ├── domain_specific_use_cases.json   # array of 3 matrices
│   ├── heinrich_39x39_use_cases.json
│   ├── mann_matrix2003_use_cases.json
│   └── triz_ai_50x50_use_cases.json
├── build_matrices.py
├── build_remaining.py
├── cross_compare.py
├── validate_matrix.py
├── triz_matrix_extraction_prompt.md
├── meta_analysis.md
├── redundancy_analysis.md
├── validation_report.md
├── validation_batch_a.md
├── validation_batch_b.md
└── validation_batch_c.md
```

### 1.2 Matrix data schema (today)

Every matrix JSON follows the same shape, defined in `triz_matrix_extraction_prompt.md`:

```json
{
  "meta":       { "name", "version", "author", "year", "domain", "dimensions", "source_url", "license", "notes" },
  "parameters": { "<id>": { "name", "description" } },
  "principles": { "<id>": { "name", "description", "sub_principles": [] } },
  "matrix":     { "<improvingId>": { "<worseningId>": [principleIds] } }
}
```

The matrix is sparse — empty cells are omitted. Cell semantics: `matrix[X][Y] = [principle IDs]` means "to improve parameter X without worsening parameter Y, try these principles."

### 1.3 What we have, by status

| File | Status | Why |
|---|---|---|
| `altshuller_39x39.json` | Canonical | Reference standard (1244 cells) |
| `altshuller_russian_original.json` | Partial duplicate | Identical cells, unique only for Russian names |
| `matriz_org_39x39.json` | Redundant | 100% identical cells + parameter names |
| `triz_agents_39x39.json` | Redundant | 100% identical cells (after fix) |
| `heinrich_39x39.json` | Unique | Curated 109-cell subset; 0% cell overlap with classic |
| `mann_matrix2003_48x48.json` | Unique | Only 48-parameter source; cells empty |
| `triz_ai_50x50.json` | Unique | Only 50-parameter source; LLM-generated |
| `drug_safety_18x18.json` | Unique | Pharmaceutical governance; 295 cells |
| `healthcare_servqual.json` | Unique | Hybrid SERVQUAL × TRIZ; 13 cells |
| `biotriz_6x6.json` | Unique | Biology-derived; includes tech comparison |
| `biotriz_24x24.json` | Partial duplicate | Same 36 cells as 6x6; unique supplementary data |
| `innovatetriz_extended.json` | Unique-ish | Bilingual; only 16 cells |

---

## 2. Problems with the Current Design

1. **No registry.** Nothing lists which matrices exist, which is canonical, and how they relate. `redundancy_analysis.md` is the closest thing — but it's prose, not data.
2. **"Purpose" is scattered across three places.** Free-text `meta.domain` + `meta.notes` inside the matrix file, plus a separate `use_cases/*.json` file, plus narrative inside `meta_analysis.md`. No single contract for what "purpose" means.
3. **Use-case schema drift.** `altshuller_39x39_use_cases.json` is a flat object; `domain_specific_use_cases.json` is an array of three matrices; `heinrich_39x39_use_cases.json` calls it `coverage_summary` while altshuller calls it `coverage_stats`. Field names diverge across files.
4. **Linkage is by filename only.** Matrix and use-case pair on the string convention `<id>.json` ↔ `<id>_use_cases.json`. No explicit `matrix_id` referenced inside files.
5. **No tags for programmatic selection.** "When to prefer / skip" prose is great for humans but unfilterable. You can't ask `domain == "software"` or `parameter_style == "service-quality"`.
6. **Redundancy is opaque inside the JSON.** `matriz_org_39x39.json` doesn't declare `identical_to: altshuller_39x39` in its own metadata — that knowledge lives only in the markdown report.

---

## 3. Proposed Design

### 3.1 Stable IDs and one canonical layout

Give every matrix a `matrix_id` (the filename stem already works: `altshuller_39x39`, `biotriz_6x6`, …). One id maps 1:1 to two files plus a registry entry:

```
matrices/<id>.json          # data: meta, parameters, principles, matrix
use_cases/<id>.json         # purpose: one schema, one file per id
registry.json               # the index — the single entry point
```

- Drop the array-of-matrices file (`domain_specific_use_cases.json`); split into three per-id files.
- Replace the `redundant/` subfolder with a `status` field on the matrix's own metadata (see §3.2).
- Each id has at most two files; nothing else.

### 3.2 Tighten the matrix `meta` block — make purpose machine-readable

Replace free-form `domain` + `notes` with structured fields. Three layers of "purpose" — identity, lineage, scope — get explicit slots:

```json
"meta": {
  "id": "altshuller_39x39",
  "name": "Classic Altshuller TRIZ Contradiction Matrix",
  "version": "1971",
  "author": "Genrich Altshuller",
  "year": "1971",
  "source_url": "https://www.triz40.com/aff_Matrix_TRIZ.php",
  "license": "Public domain",
  "dimensions": { "rows": 39, "cols": 39, "populated_cells": 1244 },

  "status": "canonical",
    // canonical | variant | derived | domain | experimental | identical-duplicate

  "lineage": {
    "derived_from": null,
    "supersedes":   [],
    "identical_to": []         // matriz_org -> ["altshuller_39x39"]
  },

  "scope": {
    "problem_class":      "engineering-contradiction",
       // engineering | service | governance | bio | software | hybrid
    "parameter_taxonomy": "altshuller-39",
    "principle_taxonomy": "altshuller-40",
    "tags": ["mechanical", "manufacturing", "physical-product"]
  },

  "notes": "..."
}
```

This lets a script answer "what matrices exist for software contradictions?" via `filter(meta.scope.tags contains 'software')`.

### 3.3 Add `registry.json` as the single entry point

A small index — not a re-derivation of all metadata, just pointers:

```json
{
  "schema_version": 1,
  "generated": "2026-05-03",
  "matrices": [
    {
      "id": "altshuller_39x39",
      "matrix_file":   "matrices/altshuller_39x39.json",
      "use_case_file": "use_cases/altshuller_39x39.json",
      "status": "canonical",
      "summary": "Classic 39×39 engineering matrix (Altshuller 1971). The reference everyone else extends or curates.",
      "tags": ["engineering", "mechanical", "canonical"]
    },
    {
      "id": "matriz_org_39x39",
      "matrix_file": "matrices/matriz_org_39x39.json",
      "status": "identical-duplicate",
      "identical_to": "altshuller_39x39",
      "summary": "Provenance copy from matriz.org. Cells and parameter names hash-identical to canonical."
    }
  ]
}
```

`redundancy_analysis.md` becomes a generated report from this registry, not the source of truth.

### 3.4 One use-case schema — what "purpose" means

Pin "purpose" down to four questions in fixed slots:

```json
{
  "matrix_id": "altshuller_39x39",
  "schema_version": 1,

  "what_it_is": "One paragraph: what this matrix encodes and how it differs from neighbors.",

  "when_to_use": {
    "ideal_user_profile": "...",
    "best_for":         ["..."],
    "not_suitable_for": ["..."],
    "prefer_over_alternatives_when": "...",
    "skip_in_favor_of": [
      { "matrix_id": "triz_ai_50x50", "if": "you need parameters for security/compatibility/sustainability" },
      { "matrix_id": "biotriz_6x6",   "if": "your problem maps cleanly to substance/structure/space/time/energy/info" }
    ]
  },

  "selector_tags": {
    "domains":         ["mechanical", "manufacturing"],
    "problem_classes": ["engineering-contradiction"],
    "excludes":        ["software", "service", "governance", "bio"]
  },

  "coverage":   { "populated_cells": 1244, "coverage_pct": 83.9 },
  "strengths":  [{ "area": "...", "why": "..." }],
  "weaknesses": [{ "area": "...", "why": "..." }]
}
```

Two upgrades over today:

- `skip_in_favor_of` makes redirection explicit and machine-followable.
- `selector_tags` is a flat, queryable filter surface separate from the human prose.

The narrative `when_to_prefer` / `when_to_skip` from existing files survives as `prefer_over_alternatives_when`.

### 3.5 Validation contract

Extend `validate_matrix.py` to enforce:

- Every `matrices/<id>.json` has a `use_cases/<id>.json` (and vice versa), unless `meta.status` says otherwise (e.g. `identical-duplicate` may skip use-case file).
- Every `skip_in_favor_of[].matrix_id` resolves to an entry in `registry.json`.
- `lineage.identical_to` claims are verified by re-hashing cells (already done by `cross_compare.py`).
- `selector_tags.domains` and `selector_tags.excludes` are disjoint.
- `meta.id` matches the filename stem.

This turns "purpose" into something CI can fail on, not prose that drifts.

---

## 4. Migration Steps

1. **Add `meta.id`, `meta.status`, `meta.lineage`, `meta.scope`** to every matrix file. Keep the existing free-form `notes` for now.
2. **Move duplicates back from `redundant/` to `matrices/`** and mark them `status: "identical-duplicate"` with `lineage.identical_to: ["altshuller_39x39"]`.
3. **Split `domain_specific_use_cases.json`** into three per-id files: `drug_safety_18x18.json`, `healthcare_servqual.json`, `innovatetriz_extended.json`.
4. **Normalize use-case schemas** to the shape in §3.4. Field renames (`coverage_summary` → `coverage`, `coverage_stats` → `coverage`) are mechanical.
5. **Add `selector_tags`** to every use-case file. This is the only manual classification step.
6. **Generate `registry.json`** from the matrix files (status, lineage, summary all already present).
7. **Extend `validate_matrix.py`** with the checks in §3.5; wire it into the build scripts.
8. **Regenerate `redundancy_analysis.md` and `meta_analysis.md`** from the new registry + matrix data so they become derived artifacts.

---

## 5a. Heterogeneity Rules (mandatory, supports plugin §13)

The corpus is not uniform. These rules normalize what the plugin's deterministic scripts can assume.

**One submatrix per file.** If a matrix file contains multiple cell tables (e.g. BioTRIZ has biology and technology submatrices), it must be split into separate files with distinct `meta.id`s. The submatrix-as-key convention (`matrix_technology` alongside `matrix`) is forbidden in v1.1+.

**Empty-cell matrices are first-class but flagged.** A matrix may ship with zero populated cells (e.g. Mann 2003 shell). It must declare `meta.dimensions.populated_cells: 0` and `meta.status: "shell"`. Stage A of selection drops shell matrices unless `--matrix=<id>` is explicit.

**Prefixed parameter IDs are allowed.** Parameter keys may be strings of any shape (e.g. `S1`, `T19`). The matrix file must declare `meta.parameter_id_style`:

```json
"parameter_id_style": "numeric"        // "1", "2", ... — classic
"parameter_id_style": "prefixed"       // "S1", "T19" — hybrid like healthcare_servqual
"parameter_id_style": "alphanumeric"   // free strings — only with explicit declaration
```

**Diagonal cells are explicit.** Most matrices skip diagonal (i==j) cells. BioTRIZ includes them. Each matrix declares `meta.diagonal_cells: "included" | "excluded"`. Lookup honors this.

**Principle taxonomy is named.** Matrices that reinterpret standard principles (e.g. drug_safety reframing "Pneumatics" as "hierarchical buffering") declare `meta.principle_taxonomy != "altshuller-40"`. The interpreter subagent reads this tag to choose its prompt strategy.

## 5b. Amendments (numbered, referenced by plugin design)

These amendments to §3 are required by `triz_workshop_design.md` and must ship as part of Phase 0.

### Amendment 1 — Structured `if` DSL on `skip_in_favor_of`

Free-text `if` is rejected at registry validation. Allowed shape:

```json
"skip_in_favor_of": [
  {
    "target_matrix_id": "triz_ai_50x50",
    "if": {
      "any_of": [
        { "exotic_signal": "security" },
        { "exotic_signal": "compatibility" }
      ]
    }
  }
]
```

**Predicates (closed set v1):** `exotic_signal`, `domain_signal`, `contradiction_type_is`, `domain_class_is`, `language_is`, `populated_cells_at_least` (integer threshold).

**Combinators (closed set v1):** `any_of`, `all_of`, `not`.

**Extension procedure:** new predicates require (a) a PR adding a parser case and unit test; (b) a `registry.json:schema_version` minor bump; (c) plugin's `compatibility.matrix_collection_schema` range update. New predicates do not break old plugins because old plugins reject unknown predicates with a clear error rather than silently ignoring them.

**Cycle detection:** redirect resolution traverses at most 3 levels. Cycles abort with a registry validation error.

### Amendment 2 — Controlled `selector_tags` vocabulary

`selector_tags.domains`, `.problem_classes`, `.tags`, and `.excludes` draw from a single controlled vocabulary file: `selector_tags_vocabulary.json` (sibling of `registry.json`). Free strings are rejected at registry validation.

```json
{
  "schema_version": 1,
  "domains":         ["mechanical", "manufacturing", "software", "service", "governance", "bio", "fintech", "healthcare", "..."],
  "problem_classes": ["engineering-contradiction", "physical-contradiction", "service-quality-gap", "governance-tension"],
  "tags":            ["physical-product", "patent-derived", "llm-generated", "curated-subset", "bilingual", "..."]
}
```

Adding a tag = PR + minor schema bump.

### Amendment 3 — `principles[<id>].canonical_id`

Every principle in every matrix file must declare a `canonical_id`. The canonical id space is shared across matrices.

```json
"principles": {
  "1": {
    "canonical_id": "P_SEGMENTATION",
    "name": "Segmentation",
    "description": "...",
    "sub_principles": [...],
    "interpretation_lineage": "altshuller-40"
      // identifies the family for interpretation-prompting:
      // "altshuller-40" | "biotriz-40" | "drug-safety-reframed" | "triz-ai-extended"
  }
}
```

`canonical_id` is used at the **principle-list dedup** layer only (do not generate a redundant interpretation when matrix A and matrix B both yield principle 1). It is **not** used to collapse interpretations — the synthesizer keeps interpretations from different `interpretation_lineage`s as distinct angles. See plugin §9.6 / §14.3 for policy.

### Amendment 4 — Language tag

Each matrix declares `meta.language` (BCP 47). Bilingual matrices declare an array.

```json
"meta": {
  "language": ["en"]
  // or ["zh", "en"] for innovatetriz_extended
}
```

The plugin's `--lang=` flag is reserved for v1.0+; v0.1 handles English only and treats non-English-only matrices as candidates only when their language array intersects `["en"]`.

### Amendment 5 — `meta.dimensions` is structured

Replace free-text `"dimensions": "39x39"` with:

```json
"dimensions": {
  "rows": 39,
  "cols": 39,
  "populated_cells": 1244
}
```

For non-square matrices (healthcare_servqual: 10×9), this carries the actual axis sizes. Validation can now compute density without parsing strings.

## 6. What This Gives You

- **One way in:** read `registry.json`, pick an id, load two files.
- **One definition of "purpose":** the `use_cases/<id>.json` schema. `meta.scope.tags` is the fast filter; the use-case file is the long form.
- **Programmatic selection:** "given a problem with tags X, rank candidate matrices" becomes a JSON filter, not a markdown read-through.
- **Honest redundancy:** duplicates declare `identical_to` in their own metadata; `redundant/` is no longer a folder, it's a status.
- **Reports stay derived:** `meta_analysis.md`, `redundancy_analysis.md`, validation batches all rebuild from registry + matrix files. No drift.
