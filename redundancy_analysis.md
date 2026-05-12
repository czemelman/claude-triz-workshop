# TRIZ Matrix Collection — Redundancy Analysis

## Cell-by-Cell Comparison: 39×39 Matrices

| Matrix A | Matrix B | Cells A | Cells B | Identical | Match |
|:---------|:---------|:-------:|:-------:|:---------:|:-----:|
| altshuller_39x39 | altshuller_russian_original | 1244 | 1244 | **1244** | **100%** |
| altshuller_39x39 | matriz_org_39x39 | 1244 | 1244 | **1244** | **100%** |
| altshuller_39x39 | triz_agents_39x39 | 1244 | 1244 | **1244** | **100%** |
| altshuller_russian_original | matriz_org_39x39 | 1244 | 1244 | **1244** | **100%** |
| altshuller_russian_original | triz_agents_39x39 | 1244 | 1244 | **1244** | **100%** |
| matriz_org_39x39 | triz_agents_39x39 | 1244 | 1244 | **1244** | **100%** |
| altshuller_39x39 | heinrich_39x39 | 1244 | 109 | **0** | **0%** |

**Finding:** altshuller, russian_original, matriz_org, and triz_agents all have **100% identical cell data**. Heinrich has completely different values (curated subset, 0% overlap).

## Other Comparisons

| Comparison | Result |
|:-----------|:-------|
| biotriz_6x6 vs biotriz_24x24 | **100% identical** (36/36 cells) — same biology matrix in both |
| triz_ai (39×39 region) vs altshuller | **17% match** (222 of 1244) — triz_ai is LLM-generated, not sourced from Altshuller |

## Parameter Names

All four 39×39 matrices (altshuller, russian, matriz, triz_agents) have **identical parameter names** (same MD5 hash).

## Unique Features per File

| Feature | Files that have it |
|:--------|:-------------------|
| Russian parameter names (`name_ru`) | altshuller_russian_original only |
| Rich principle sub_principles | altshuller, russian, matriz, triz_agents, heinrich, mann, biotriz (both), healthcare, triz_ai (10 files) |
| Extended parameters (40-50) | triz_ai only (11 modern params) |
| 48 parameters | mann only |
| Domain-specific parameters | drug_safety (18 governance), healthcare (19 hybrid), innovatetriz (18 bilingual) |
| Biology + technology dual matrices | biotriz_6x6, biotriz_24x24 |
| Supplementary data (similarity, NEPs, frequency) | biotriz_24x24 only |

## Redundancy Verdicts

| File | Verdict | Reasoning |
|:-----|:--------|:----------|
| **altshuller_39x39.json** | **CANONICAL** | Reference standard. Keep. |
| **altshuller_russian_original.json** | **PARTIALLY REDUNDANT** | 100% identical cells. Only unique value: Russian names (`name_ru`). |
| **matriz_org_39x39.json** | **REDUNDANT** | 100% identical cells AND identical parameter names to altshuller. No unique metadata. |
| **triz_agents_39x39.json** | **REDUNDANT** | 100% identical cells (we replaced its broken matrix with altshuller's). Principle descriptions match standard. |
| **heinrich_39x39.json** | **UNIQUE** | Completely different cell values (0% overlap). Curated 109-cell subset with independent analysis. |
| **mann_matrix2003_48x48.json** | **UNIQUE** | Only source with 48 parameters (9 beyond classic 39). No cell data — parameters/principles shell only. |
| **triz_ai_50x50.json** | **UNIQUE** | Only 50-param matrix. 2345 cells. LLM-generated but unique data. 11 modern extension parameters. |
| **drug_safety_18x18.json** | **UNIQUE** | Only pharmaceutical governance matrix. 18 domain-specific parameters, 295 cells. |
| **healthcare_servqual.json** | **UNIQUE** | Only healthcare service quality matrix. Hybrid SERVQUAL×TRIZ. 13 cells. |
| **biotriz_6x6.json** | **UNIQUE** | Biology-derived contradiction resolution. 6 operational fields. Includes technology comparison matrix. |
| **biotriz_24x24.json** | **PARTIALLY REDUNDANT** | Same 36 biology cells as biotriz_6x6. Unique value: supplementary data (similarity matrix, NEPs, frequency analysis, parameter mappings). |
| **innovatetriz_extended.json** | **UNIQUE** | Bilingual Chinese/English. Custom 18 parameters. Only 16 cells but unique domain framing. |

## Recommendation

### Keep (8 files — the canonical collection):
1. `altshuller_39x39.json` — canonical reference
2. `altshuller_russian_original.json` — unique Russian names (merge `name_ru` into canonical if preferred)
3. `heinrich_39x39.json` — independent curated analysis
4. `mann_matrix2003_48x48.json` — only 48-param source
5. `triz_ai_50x50.json` — only 50-param source (with LLM caveat)
6. `drug_safety_18x18.json` — unique domain
7. `healthcare_servqual.json` — unique domain
8. `biotriz_6x6.json` — unique domain (biology)

### Could remove without data loss (4 files):
1. `matriz_org_39x39.json` — 100% duplicate of altshuller, no unique metadata
2. `triz_agents_39x39.json` — 100% duplicate of altshuller (after our fix)
3. `biotriz_24x24.json` — same cells as biotriz_6x6 (merge supplementary data into 6x6 if desired)
4. `innovatetriz_extended.json` — only 16 cells, minimal unique value (keep if bilingual matters)

### Alternative: merge instead of delete
- Merge `name_ru` from russian_original into altshuller → delete russian_original
- Merge supplementary from biotriz_24x24 into biotriz_6x6 → delete 24x24
- Keep matriz_org and triz_agents as "provenance variants" if source attribution matters
