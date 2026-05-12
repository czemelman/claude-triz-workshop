# TRIZ Matrix Validation Report -- Batch C

**Date:** 2026-03-26
**Files validated:** 4
**Reference matrix:** `matrices/altshuller_39x39.json`

---

## File 9: healthcare_servqual.json

**Summary:** Hybrid SERVQUAL x TRIZ contradiction matrix (10 x 9, 13 populated cells, 17 principles). Two heterogeneous parameter sets distinguished by S-prefix (SERVQUAL) and T-prefix (TRIZ).

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| A1. `meta` object with all required fields | **PASS** | All 9 required fields present. Also has extra `doi` field. |
| A2. `parameters` object, all keys strings | **FAIL** | No `parameters` key. Uses `improving_parameters` and `worsening_parameters` instead. |
| A3. `principles` object, keys strings, each has name/description/sub_principles | **PASS** | 17 principles, all with required fields. Keys are strings. |
| A4. `matrix` is sparse (nested objects) | **PASS** | Standard sparse nested-object structure. |
| A5. All matrix keys are strings | **PASS** | Outer keys: "S1"-"S10". Inner keys: "T9","T19","T25","T26","T27","T28","T29","T34","T36". |
| A6. All matrix cell values are arrays of integers | **PASS** | All 13 cells contain arrays of integers. |

### B. Data Integrity

| Check | Result | Details |
|-------|--------|---------|
| B1. All principle IDs in cells exist in `principles` | **PASS** | All referenced principle IDs (1,2,4,10,13,14,18,22,24,25,26,28,30,32,34,35,36) found. |
| B2. All parameter IDs in matrix exist in parameters | **PASS** | All S-prefix and T-prefix keys found in their respective parameter objects. |
| B3. No self-referencing (diagonal) cells | **PASS** | Heterogeneous axes (S vs T) -- diagonal concept does not apply. |
| B4. No empty arrays in cells | **PASS** | |
| B5. No duplicate principle IDs within a cell | **PASS** | |

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| C1. Non-standard parameter keys | **FAIL** | Uses `improving_parameters` and `worsening_parameters` instead of `parameters`. |
| C2. Alternative matrix structure | **PASS** | Standard sparse structure. |
| C3. Extra top-level keys | **INFO** | Extra keys: `improving_parameters`, `worsening_parameters`. No standard `parameters` key. Also has `doi` in meta (non-standard but informative). |
| C4. Hybrid parameter handling | **INFO** | The two parameter types are separated into distinct top-level objects. Improving parameters (rows) use "S" prefix and originate from SERVQUAL. Worsening parameters (columns) use "T" prefix and originate from classical TRIZ. Each parameter object includes an `origin` field ("SERVQUAL", "SERVQUAL (sub-dimension)", or "TRIZ") and worsening parameters include a `classical_triz_number` field. This design is a reasonable accommodation for the hybrid matrix but deviates from the unified schema's single `parameters` object. |

---

## File 10: innovatetriz_extended.json

**Summary:** Custom simplified 18-parameter matrix from the InnovateTRIZ project, with 16 sparse entries and all 40 TRIZ principles. Bilingual (Chinese/English). Parameters are custom, not standard Altshuller.

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| A1. `meta` object with all required fields | **PASS** | All 9 required fields present. |
| A2. `parameters` object, all keys strings | **PASS** | 18 parameters, all with string keys ("1"-"18"). |
| A3. `principles` object, keys strings, each has name/description/sub_principles | **PASS** | 40 principles, all with required fields. All `sub_principles` are present but are empty arrays `[]`. Keys are strings. |
| A4. `matrix` is sparse (nested objects) | **PASS** | |
| A5. All matrix keys are strings | **PASS** | |
| A6. All matrix cell values are arrays of integers | **PASS** | |

### B. Data Integrity

| Check | Result | Details |
|-------|--------|---------|
| B1. All principle IDs in cells exist in `principles` | **PASS** | All referenced IDs (1-40 range) are defined. |
| B2. All parameter IDs in matrix exist in `parameters` | **PASS** | All row/column keys map to defined parameters. |
| B3. No self-referencing (diagonal) cells | **PASS** | |
| B4. No empty arrays in cells | **PASS** | |
| B5. No duplicate principle IDs within a cell | **PASS** | |

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| C1. Non-standard parameter keys | **PASS** | Uses standard `parameters` key. |
| C2. Alternative matrix structure | **PASS** | Standard sparse structure. |
| C3. Extra top-level keys | **INFO** | Has `_matrix_key_legend` -- a documentation-only object mapping parameter IDs to their original Chinese names and explaining the source format. Prefixed with underscore to signal metadata. |
| C4. Additional parameter fields | **INFO** | Parameters include non-standard fields: `name_zh`, `keywords`. Principles include extensive extra fields: `name_zh`, `description_zh`, `detailed`, `detailed_zh`, `examples`, `examples_zh`, `applications`, `applications_zh`, `implementation_steps`, `benefits`, `category`, `category_zh`. All `sub_principles` arrays are empty (all sub-principle content is in the `detailed` fields instead). |

---

## File 11: triz_agents_39x39.json

**Summary:** Classic 39-parameter, 40-principle matrix from the TRIZ-Agents multi-agent LLM system. 1248 populated cells. Intended to be the standard Altshuller matrix but has significant column-numbering errors in 22 of 39 rows.

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| A1. `meta` object with all required fields | **PASS** | All 9 required fields present. |
| A2. `parameters` object, all keys strings | **PASS** | 39 parameters, all string keys. |
| A3. `principles` object, keys strings, each has name/description/sub_principles | **PASS** | 40 principles, all with required fields. |
| A4. `matrix` is sparse (nested objects) | **PASS** | |
| A5. All matrix keys are strings | **PASS** | |
| A6. All matrix cell values are arrays of integers | **PASS** | |

### B. Data Integrity

| Check | Result | Details |
|-------|--------|---------|
| B1. All principle IDs in cells exist in `principles` | **PASS** | |
| B2. All parameter IDs in matrix exist in `parameters` | **PASS** | |
| B3. No self-referencing (diagonal) cells | **PASS** | |
| B4. No empty arrays in cells | **PASS** | |
| B5. No duplicate principle IDs within a cell | **FAIL** | Cell [19][9] contains `[8, 35, 35]` -- principle 35 is duplicated. |
| B7. 5 random cells vs altshuller_39x39.json | **FAIL** | Compared 5 randomly sampled cells (seed=42). 3 matched, 2 mismatched. Deeper analysis reveals a **systematic column-numbering offset bug** affecting 22 of 39 rows (see details below). |

**Column-offset bug detail:** The source Excel extraction appears to have introduced off-by-one (and occasionally off-by-two) column shifts. The pattern:

- **17 rows match perfectly:** rows 2, 9, 10, 11, 13, 14, 18, 23, 26, 32, 33, 34, 35, 36, 37, 38, 39.
- **22 rows have shifted columns:** rows 1, 3, 4, 5, 6, 7, 8, 12, 15, 16, 17, 19, 20, 21, 22, 24, 25, 27, 28, 29, 30, 31.
- In affected rows, data values are correct but assigned to wrong column keys. For example, in row 1: columns 3-19 match altshuller directly, but columns 21-39 each contain the data that belongs one column earlier (agents col 21 = altshuller col 20, agents col 22 = altshuller col 21, etc.). Column 20 is missing entirely. Row 3 shows a delta=+1 shift starting earlier (from col 5) that becomes delta=+2 from col 14 onward, indicating the source skipped two columns during extraction.
- **Root cause:** Likely an extraction artifact from `triz_matrix.xls` where empty diagonal cells or hidden columns caused column indices to shift.
- **Impact:** 296 cells directly mismatched at their stated coordinates (23.7% of 1248 cells); the actual principle data is present but mislabeled.

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| C1. Non-standard parameter keys | **PASS** | |
| C2. Alternative matrix structure | **PASS** | |
| C3. Extra top-level keys | **PASS** | Only standard keys: meta, parameters, principles, matrix. |

---

## File 12: triz_ai_50x50.json

**Summary:** Extended 50-parameter, 40-principle matrix from the triz-ai project (v0.14.0). Parameters 1-39 are Altshuller classic; 40-50 cover modern domains. 2345 populated cells total. The classic 39x39 region is densely filled (1482 cells vs altshuller's 1244) with substantially different values -- the matrix appears to be an independent LLM-generated reconstruction, not a faithful copy of Altshuller's original data.

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| A1. `meta` object with all required fields | **PASS** | All 9 required fields present. |
| A2. `parameters` object, all keys strings | **PASS** | 50 parameters, all string keys ("1"-"50"). |
| A3. `principles` object, keys strings, each has name/description/sub_principles | **PASS** | 40 principles, all with required fields. |
| A4. `matrix` is sparse (nested objects) | **PASS** | |
| A5. All matrix keys are strings | **PASS** | |
| A6. All matrix cell values are arrays of integers | **PASS** | |

### B. Data Integrity

| Check | Result | Details |
|-------|--------|---------|
| B1. All principle IDs in cells exist in `principles` | **PASS** | |
| B2. All parameter IDs in matrix exist in `parameters` | **PASS** | |
| B3. No self-referencing (diagonal) cells | **PASS** | |
| B4. No empty arrays in cells | **PASS** | |
| B5. No duplicate principle IDs within a cell | **FAIL** | 9 cells contain duplicate principle IDs: `[10][47]: [23,23,24,6]`, `[14][48]: [15,23,10,23]`, `[17][46]: [35,36,39,39]`, `[22][46]: [22,39,39,23]`, `[33][41]: [18,15,29,29]`, `[40][39]: [39,39,28,25]`, `[42][41]: [18,18,39,34]`, `[50][25]: [25,19,4,19]`, `[50][26]: [26,4,30,30]`. All 9 involve extended parameters (40-50), consistent with LLM-generated data having occasional repetitions. |
| B6. First 39 params consistent with Altshuller names | **FAIL (minor)** | 2 of 39 parameter names have minor wording differences: param 15 uses "Duration of action **by a** moving object" vs Altshuller's "Duration of action **of** moving object"; param 16 uses "Duration of action **by a** stationary object" vs "Duration of action **of** stationary object". All other 37 names match. |

**Classic region accuracy:** Only 17.6% of the 1244 cells that exist in both the triz_ai classic region (params 1-39) and the altshuller reference have identical values. The triz_ai matrix fills 1482 cells in the 39x39 region (238 more than altshuller), and the values in shared positions are largely different. This confirms the meta's description that the matrix was computationally generated rather than transcribed from the original. The meta states "Cells for params 40-50 were LLM-seeded," but the data shows the entire matrix (including the classic 1-39 region) has been regenerated.

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| C1. Non-standard parameter keys | **PASS** | |
| C2. Alternative matrix structure | **PASS** | |
| C3. Extra top-level keys | **PASS** | Only standard keys: meta, parameters, principles, matrix. |

---

## Summary Table

| Check | healthcare_servqual | innovatetriz_extended | triz_agents_39x39 | triz_ai_50x50 |
|-------|:---:|:---:|:---:|:---:|
| **A. Schema Compliance** | | | | |
| A1. meta complete | PASS | PASS | PASS | PASS |
| A2. parameters present & string keys | FAIL | PASS | PASS | PASS |
| A3. principles valid | PASS | PASS | PASS | PASS |
| A4. matrix sparse objects | PASS | PASS | PASS | PASS |
| A5. matrix keys strings | PASS | PASS | PASS | PASS |
| A6. cell values arrays of ints | PASS | PASS | PASS | PASS |
| **B. Data Integrity** | | | | |
| B1. principle IDs valid | PASS | PASS | PASS | PASS |
| B2. parameter IDs valid | PASS | PASS | PASS | PASS |
| B3. no diagonal | PASS | PASS | PASS | PASS |
| B4. no empty arrays | PASS | PASS | PASS | PASS |
| B5. no duplicate IDs in cell | PASS | PASS | FAIL (1 cell) | FAIL (9 cells) |
| B6. first-39 param names | n/a | n/a | n/a | FAIL (minor, 2) |
| B7. 5 random cells vs altshuller | n/a | n/a | FAIL (2/5) | n/a |
| **C. Schema Deviations** | | | | |
| C1. non-standard param keys | FAIL | PASS | PASS | PASS |
| C2. matrix structure | PASS | PASS | PASS | PASS |
| C3. extra top-level keys | INFO (2) | INFO (1) | PASS | PASS |

### Key Findings

1. **healthcare_servqual** uses `improving_parameters` / `worsening_parameters` instead of a single `parameters` object -- a deliberate design choice to handle the hybrid SERVQUAL x TRIZ parameter axes. Schema-incompatible but data-sound.

2. **innovatetriz_extended** is fully schema-compliant. The only note is `_matrix_key_legend` (extra documentation key) and empty `sub_principles` arrays in all 40 principles (sub-principle content is stored in `detailed` fields instead).

3. **triz_agents_39x39** has a systematic **column-numbering offset bug** originating from the Excel extraction. 22 of 39 rows have shifted column assignments, affecting 296 cells (23.7%). The data values themselves are from the real Altshuller matrix but are assigned to wrong column keys. Also has 1 cell with a duplicate principle ID.

4. **triz_ai_50x50** has 9 cells with duplicate principle IDs (all in the extended parameter region, likely LLM artifacts). The classic 39x39 region matches only 17.6% of altshuller cells, indicating the entire matrix was LLM-generated despite the meta implying only params 40-50 were LLM-seeded. Two minor parameter name differences ("by a" vs "of").
