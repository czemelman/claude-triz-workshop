# TRIZ Matrix Validation Report -- Batch B

**Date:** 2026-03-26
**Files validated:** 4
**Schema basis:** Unified canonical schema (meta / parameters / principles / matrix)

---

## File 5: mann_matrix2003_48x48.json

**Path:** `matrices/mann_matrix2003_48x48.json`
**Summary:** 48 parameters, 40 principles, matrix is EMPTY (no cell data).

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| `meta` object present | **PASS** | |
| `meta` required fields (name, version, author, year, domain, dimensions, source_url, license, notes) | **PASS** | All 9 fields present |
| `meta` extra fields | PASS | None |
| `parameters` object present | **PASS** | 48 parameters |
| `parameters` keys are strings | **PASS** | "1" through "48" |
| `principles` object present | **PASS** | 40 principles |
| `principles` keys are strings | **PASS** | "1" through "40" |
| `principles` entries have name/description/sub_principles | **PASS** | All 40 conform |
| `matrix` key present | **PASS** | Key exists |
| `matrix` is sparse (nested objects) | **N/A** | Matrix is empty `{}` |
| `matrix` keys are strings | **N/A** | Matrix is empty |
| `matrix` cell values are arrays of integers | **N/A** | Matrix is empty |

### B. Data Integrity

| Check | Result | Details |
|-------|--------|---------|
| Principle IDs in matrix exist in `principles` | **N/A** | Matrix is empty |
| Parameter IDs as matrix keys exist in `parameters` | **N/A** | Matrix is empty |
| Self-referencing (diagonal) cells | **N/A** | Matrix is empty |
| Empty arrays in matrix cells | **N/A** | Matrix is empty |
| Duplicate principle IDs within cells | **N/A** | Matrix is empty |

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| Non-standard parameter keys | **PASS** | Uses canonical `parameters` |
| Alternative matrix structures | **PASS** | Uses canonical `matrix` |
| Extra top-level keys | **PASS** | Only meta/parameters/principles/matrix |
| **WARNING** | **EMPTY MATRIX** | `matrix` key exists but contains `{}`. The meta notes explain: "MATRIX CELL DATA COULD NOT BE EXTRACTED" from the source PDF. This file is a parameter/principle shell only. |

---

## File 6: biotriz_6x6.json

**Path:** `matrices/biotriz_6x6.json`
**Summary:** 6 parameters (operational fields), 40 principles, TWO matrices (biology + technology). No canonical `matrix` key.

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| `meta` object present | **PASS** | |
| `meta` required fields | **PASS** | All 9 fields present |
| `meta` extra fields | PASS | None |
| `parameters` object present | **PASS** | 6 parameters |
| `parameters` keys are strings | **PASS** | "1" through "6" |
| `principles` object present | **PASS** | 40 principles |
| `principles` keys are strings | **PASS** | "1" through "40" |
| `principles` entries have name/description/sub_principles | **PASS** | All 40 conform |
| `matrix` key present | **FAIL** | No `matrix` key. Uses `matrix_technology` and `matrix_biology` instead. |
| `matrix_biology` is sparse | **PASS** | Nested string-keyed objects |
| `matrix_biology` keys are strings | **PASS** | |
| `matrix_biology` values are int arrays | **PASS** | |
| `matrix_technology` is sparse | **PASS** | Nested string-keyed objects |
| `matrix_technology` keys are strings | **PASS** | |
| `matrix_technology` values are int arrays | **PASS** | |

### B. Data Integrity

**matrix_biology:**

| Check | Result | Details |
|-------|--------|---------|
| Principle IDs in cells exist in `principles` | **PASS** | All referenced IDs (1-40) found |
| Parameter IDs as keys exist in `parameters` | **PASS** | All row/column keys are "1"-"6" |
| Self-referencing (diagonal) cells | **FAIL** | Diagonal cells present for ALL 6 parameters: "1"-"1", "2"-"2", ..., "6"-"6". Intentional per meta notes: "Diagonal cells are included as they represent same-field contradictions." |
| Empty arrays | **PASS** | None |
| Duplicate principle IDs within cells | **PASS** | None |

**matrix_technology:**

| Check | Result | Details |
|-------|--------|---------|
| Principle IDs in cells exist in `principles` | **PASS** | |
| Parameter IDs as keys exist in `parameters` | **PASS** | |
| Self-referencing (diagonal) cells | **FAIL** | Same as biology: all 6 diagonal cells populated. Intentional by design. |
| Empty arrays | **PASS** | None |
| Duplicate principle IDs within cells | **PASS** | None |

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| Non-standard parameter keys | **PASS** | Uses canonical `parameters` |
| Alternative matrix structures | **DEVIATION** | Uses `matrix_technology` and `matrix_biology` instead of `matrix`. This is a domain-specific design choice: the file contains two parallel matrices for cross-domain comparison. |
| Extra top-level keys | **DEVIATION** | `matrix_biology`, `matrix_technology` (2 extra keys) |

---

## File 7: biotriz_24x24.json

**Path:** `matrices/biotriz_24x24.json`
**Summary:** Despite the filename "24x24", this is actually a **6x6** matrix (same data as biotriz_6x6.json with extensive annotations). Contains 6 parameters, 40 principles, 3 matrix-like objects, and 4 extra annotation keys.

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| `meta` object present | **PASS** | |
| `meta` required fields | **PASS** | All 9 fields present |
| `meta` extra fields | INFO | 5 extra fields: `dataset_scope`, `doi`, `key_finding`, `related_files`, `similarity_to_classical_triz` |
| `parameters` object present | **PASS** | 6 parameters (NOT 24) |
| `parameters` keys are strings | **PASS** | "1" through "6" |
| `parameters` entries extra fields | INFO | Non-standard fields: `classical_triz_parameters_approximate` (array of ints), `type` (string) |
| `principles` object present | **PASS** | 40 principles |
| `principles` keys are strings | **PASS** | "1" through "40" |
| `principles` entries have name/description/sub_principles | **PASS** | All 40 conform |
| `principles` entries extra fields | INFO | Non-standard field: `bio_relevance` (string) on every principle |
| `matrix` key present | **FAIL** | No `matrix` key. Uses `matrix_biology`, `matrix_technology`, and `similarity_matrix`. |
| `matrix_biology` is sparse | **PASS** | |
| `matrix_biology` keys are strings | **PASS** | |
| `matrix_biology` values are int arrays | **PASS** | |
| `matrix_technology` is sparse | **PASS** | |
| `matrix_technology` keys are strings | **PASS** | |
| `matrix_technology` values are int arrays | **PASS** | |
| `similarity_matrix` is sparse | **PASS** | |
| `similarity_matrix` keys are strings | **PASS** | |
| `similarity_matrix` values are int arrays | **FAIL** | Cell values are **floats** (0.0-1.0 similarity scores), not arrays of integers. This is a different data type -- a similarity/correlation matrix, not a contradiction matrix. |

### B. Data Integrity

**matrix_biology:**

| Check | Result | Details |
|-------|--------|---------|
| Principle IDs in cells exist in `principles` | **PASS** | |
| Parameter IDs as keys exist in `parameters` | **PASS** | |
| Self-referencing (diagonal) cells | **FAIL** | All 6 diagonal cells populated. Intentional (same-field contradictions). |
| Empty arrays | **PASS** | |
| Duplicate principle IDs within cells | **PASS** | |

**matrix_technology:**

| Check | Result | Details |
|-------|--------|---------|
| Principle IDs in cells exist in `principles` | **PASS** | |
| Parameter IDs as keys exist in `parameters` | **PASS** | |
| Self-referencing (diagonal) cells | **FAIL** | All 6 diagonal cells populated. Intentional. |
| Empty arrays | **PASS** | |
| Duplicate principle IDs within cells | **PASS** | |

**similarity_matrix:**

| Check | Result | Details |
|-------|--------|---------|
| Principle IDs in cells exist in `principles` | **PASS** | (values are floats, not principle refs -- this check is structurally inapplicable) |
| Parameter IDs as keys exist in `parameters` | **PASS** | Row/column keys "1"-"6" match parameters |
| Self-referencing (diagonal) cells | **FAIL** | All 6 diagonal cells populated. Expected for a similarity matrix. |
| Empty arrays | **PASS** | N/A (values are floats) |
| Duplicate principle IDs within cells | **PASS** | N/A (values are floats) |

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| Non-standard parameter keys | **PASS** | Uses canonical `parameters` |
| Alternative matrix structures | **DEVIATION** | Uses `matrix_biology`, `matrix_technology`, `similarity_matrix` -- no canonical `matrix` key |
| Extra top-level keys | **DEVIATION** | 6 extra keys: `biological_principle_frequency_notes`, `matrix_biology`, `matrix_technology`, `neps_28_notes`, `parameters_39_to_6_mapping_notes`, `similarity_matrix` |
| **WARNING** | **FILENAME MISMATCH** | File is named `biotriz_24x24.json` but meta.dimensions = "6x6 (operational fields)" and actual data is 6x6. The meta notes explicitly state: "A 24x24 BioTRIZ matrix does not exist in the published literature." |

---

## File 8: drug_safety_18x18.json

**Path:** `matrices/drug_safety_18x18.json`
**Summary:** 18 governance-specific parameters, 39 principles (principle 7 missing), 295 populated cells out of 306 possible off-diagonal cells. Best canonical conformance of the batch.

### A. Schema Compliance

| Check | Result | Details |
|-------|--------|---------|
| `meta` object present | **PASS** | |
| `meta` required fields | **PASS** | All 9 fields present |
| `meta` extra fields | INFO | 3 extra fields: `journal`, `source_doi`, `source_title` |
| `parameters` object present | **PASS** | 18 parameters |
| `parameters` keys are strings | **PASS** | "1" through "18" |
| `principles` object present | **PASS** | 39 principles (not 40) |
| `principles` keys are strings | **PASS** | "1" through "40" excluding "7" |
| `principles` entries have name/description/sub_principles | **PASS** | All 39 have all 3 fields; most have empty description and empty sub_principles array |
| `matrix` key present | **PASS** | |
| `matrix` is sparse (nested objects) | **PASS** | |
| `matrix` keys are strings | **PASS** | All row and column keys are strings |
| `matrix` cell values are arrays of integers | **PASS** | All values are arrays of integers |

### B. Data Integrity

| Check | Result | Details |
|-------|--------|---------|
| Principle IDs in cells exist in `principles` | **PASS** | All referenced principle IDs (1-6, 8-40) exist in `principles`. Principle 7 is neither defined nor referenced. |
| Parameter IDs as keys exist in `parameters` | **PASS** | All matrix row/column keys are valid parameter IDs |
| Self-referencing (diagonal) cells | **PASS** | No diagonal cells. Diagonal represents physical contradictions (marked "+" in original paper) and correctly excluded from sparse representation. |
| Empty arrays | **PASS** | None |
| Duplicate principle IDs within cells | **FAIL** | 2 cells contain duplicate principle IDs: |
| | | `matrix[4][6]` = [30, 14, **10, 10**] -- principle 10 appears twice |
| | | `matrix[4][11]` = [**10, 10**, 16] -- principle 10 appears twice |

### C. Schema Deviations

| Check | Result | Details |
|-------|--------|---------|
| Non-standard parameter keys | **PASS** | Uses canonical `parameters` |
| Alternative matrix structures | **PASS** | Uses canonical `matrix` |
| Extra top-level keys | **PASS** | Only meta/parameters/principles/matrix |
| Missing principle | INFO | Principle ID "7" (Nested doll) is absent from the `principles` object. This appears intentional -- the paper does not use principle 7 in any matrix cell, likely because "Nested doll" has no meaningful governance interpretation. |

---

## Summary Table

| Check | Mann 48x48 | BioTRIZ 6x6 | BioTRIZ 24x24 | Drug Safety 18x18 |
|-------|:----------:|:------------:|:--------------:|:------------------:|
| **A. Schema Compliance** | | | | |
| meta present + complete | PASS | PASS | PASS | PASS |
| parameters present + string keys | PASS | PASS | PASS | PASS |
| principles present + string keys | PASS | PASS | PASS | PASS |
| principles have required fields | PASS | PASS | PASS | PASS |
| canonical `matrix` key exists | PASS | **FAIL** | **FAIL** | PASS |
| matrix is sparse with string keys | N/A (empty) | PASS | PASS | PASS |
| matrix values are int arrays | N/A (empty) | PASS | PASS* | PASS |
| **B. Data Integrity** | | | | |
| Principle refs valid | N/A | PASS | PASS | PASS |
| Parameter refs valid | N/A | PASS | PASS | PASS |
| No diagonal cells | N/A | **FAIL** (intentional) | **FAIL** (intentional) | PASS |
| No empty arrays | N/A | PASS | PASS | PASS |
| No duplicate IDs in cells | N/A | PASS | PASS | **FAIL** (2 cells) |
| **C. Schema Deviations** | | | | |
| No non-standard param keys | PASS | PASS | PASS | PASS |
| Uses canonical `matrix` | PASS | **DEVIATION** | **DEVIATION** | PASS |
| No extra top-level keys | PASS | **DEVIATION** (2) | **DEVIATION** (6) | PASS |

*`similarity_matrix` in biotriz_24x24.json contains floats, not int arrays -- this is a fundamentally different data structure (similarity scores, not contradiction principles).

---

## Critical Issues Requiring Attention

1. **drug_safety_18x18.json -- Duplicate principle IDs in 2 cells:**
   - `matrix["4"]["6"]` = `[30, 14, 10, 10]` -- principle 10 duplicated
   - `matrix["4"]["11"]` = `[10, 10, 16]` -- principle 10 duplicated
   - These are likely data entry errors from the source paper.

2. **mann_matrix2003_48x48.json -- Empty matrix:**
   - The `matrix` object is `{}`. The file is a parameter/principle shell only. Source data was not extractable from PDF format.

3. **biotriz_24x24.json -- Misleading filename:**
   - File is named "24x24" but actual content is 6x6. The meta notes explicitly state a 24x24 BioTRIZ matrix does not exist in published literature.

4. **biotriz_6x6.json and biotriz_24x24.json -- No canonical `matrix` key:**
   - Both use `matrix_biology` and `matrix_technology` instead of `matrix`. This is a deliberate domain design choice (two parallel matrices for cross-domain comparison) but breaks canonical schema expectations.

5. **biotriz_6x6.json and biotriz_24x24.json -- Diagonal cells intentionally populated:**
   - All 6 diagonal cells contain data in both biology and technology matrices. The meta notes document this as intentional ("same-field contradictions"). Standard TRIZ matrices exclude diagonals.

6. **drug_safety_18x18.json -- Principle 7 missing from principles object:**
   - The standard set of 40 TRIZ principles is defined as 1-40, but principle 7 ("Nested doll") is absent. It is also not referenced in any matrix cell, so no referential integrity issue exists.
