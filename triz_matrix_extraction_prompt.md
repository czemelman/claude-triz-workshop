# Task: Extract All Publicly Available TRIZ Contradiction Matrices into Validated JSON Files

## Objective

Extract every TRIZ contradiction matrix available from the sources listed below into individual, self-contained JSON files following a strict schema. Each file must be independently validated against its source before being considered complete. This is for personal research and meta-analysis — no publication.

## Output Schema

Every matrix file must follow this exact structure:

```json
{
  "meta": {
    "name": "",
    "version": "",
    "author": "",
    "year": "",
    "domain": "",
    "dimensions": "",
    "source_url": "",
    "license": "",
    "notes": ""
  },
  "parameters": {
    "1": {
      "name": "",
      "description": ""
    }
  },
  "principles": {
    "1": {
      "name": "",
      "description": "",
      "sub_principles": []
    }
  },
  "matrix": {
    "1": {
      "2": [15, 8, 29, 34]
    }
  }
}
```

**Schema rules:**
- All keys are strings, including numeric IDs
- matrix is sparse — only include cells that contain principle recommendations, skip empty cells entirely
- matrix."X"."Y" means: improving parameter X, worsening parameter Y -> list of recommended principle IDs
- Principle IDs in the matrix cells are integers inside an array
- parameters must include every parameter used on both axes
- principles must include every principle referenced in any matrix cell
- sub_principles is an array of strings, one per sub-principle (e.g., "a) Divide into independent parts")
- If a source does not provide descriptions or sub-principles, use empty strings or empty arrays — do not fabricate content

## Sources to Extract (process each one as a separate file)

### File 1: altshuller_39x39.json
**Source:** https://www.triz40.com/aff_Matrix_TRIZ.php
**What:** Classic Altshuller 39x39 matrix — the original public domain version
**Extract:** All 39 parameters (names), all 40 principles (names + sub-principles), full matrix cell data
**Supplement principle descriptions from:** https://www.triz40.com/aff_Principles_TRIZ.php (same site has all 40 principles with sub-principles and examples)

### File 2: altshuller_39x39_excel.json
**Source:** https://innovation-triz.com/triz40/triz_matrix.xls
**What:** Excel version of the same classic matrix — use this as a cross-check against File 1
**Extract:** Full matrix cell data, all parameters
**Note:** After extraction, diff against File 1 to verify they match. Document any discrepancies in meta.notes

### File 3: mann_matrix2003_48x48.json
**Source:** https://www.triz-consulting.de/about-triz/triz-matrix/?lang=en (Excel heatmap download available on this page)
**Also check:** https://arvindvenkatadri.com/pdf/TRIZ/ContradictionMatrix2003.pdf (PDF poster of Matrix 2003)
**What:** Darrell Mann's updated 48x48 matrix with extended parameters
**Extract:** All 48 parameters (with category groupings if available), full matrix cell data, any new/combination principles beyond the standard 40

### File 4: biotriz_6x6.json
**Source:** https://pmc.ncbi.nlm.nih.gov/articles/PMC1664643/
**What:** BioTRIZ / PRIZM matrix by Vincent, Bogatyreva et al. — 6 operational fields for biology vs technology
**Extract:** The 6 parameters (Substance, Structure, Space, Time, Energy, Information), both the technology matrix AND the biology matrix (store as two separate matrix objects in the file — e.g., "matrix_technology" and "matrix_biology"), the biological inventive principles if they differ from standard 40
**Note:** This paper contains TWO matrices — one for how technology solves problems, one for how biology solves them. Extract both.

### File 5: rcm_performance_13x13.json
**Source:** https://www.osaka-gu.ac.jp/php/nakagawa/TRIZ/eTRIZ/epapers/e2011Papers/eMiharaTRIZSymp2010/eMihara-TRIZSymp2010-110921.html
**What:** Japanese Redesigned Contradiction Matrix — performance-related parameters
**Extract:** 13 performance parameters, matrix cell data

### File 6: rcm_shape_11x11.json
**Source:** Same as File 5
**What:** Japanese Redesigned Contradiction Matrix — shape/design parameters
**Extract:** 11 shape/design parameters, matrix cell data

### File 7: triz_am_8x8.json
**Source:** https://www.researchgate.net/publication/328709547
**What:** Additive Manufacturing specific TRIZ matrix by Renjith et al.
**Extract:** 8 AM-specific parameters, matrix cell data, any modified principles

### File 8: heinrich_39x39.json
**Source:** https://github.com/NickScherbakov/Heinrich-The-Inventing-Machine
**What:** Python/JSON knowledge base — Apache 2.0 licensed, includes matrix + scientific effects
**Extract:** Matrix data, parameters, principles from the repo's knowledge base files
**Note:** This repo may already have data in a structured format — adapt to our schema rather than re-entering

### File 9: matriz_org_39x39.json
**Source:** https://wiki.matriz.org/docs/triz-tools/contradictions-matrix/
**What:** MATRIZ organization's official interactive matrix
**Extract:** Full matrix data (may need to inspect page JavaScript/network requests)
**Note:** Cross-check against File 1 for consistency

### File 10: altshuller_russian_original.json
**Source:** https://www.altshuller.ru/triz/technique2.asp
**What:** Russian original from Altshuller Foundation website
**Extract:** Parameter names in both Russian and English, matrix cell data
**Note:** This is the authoritative original — useful for verifying translations in other files

### File 11: wipo_39x39.json
**Source:** https://www.wipo.int/documents/d/tisc/docs-en-tisc-toolkit-triz-description.pdf
**What:** WIPO's TRIZ toolkit — should contain a matrix in the PDF/workbook
**Extract:** Whatever matrix data is available in the PDF/workbook

### File 12: healthcare_servqual.json
**Source:** https://pmc.ncbi.nlm.nih.gov/articles/PMC4796413/
**What:** Healthcare SERVQUAL-TRIZ parameter mapping
**Extract:** The parameter mapping table and any matrix-like data available
**Note:** This may be a partial mapping rather than a full matrix — extract whatever is available

## Additional Sources to Search For (may or may not be extractable)

- Oxford TRIZ matrix: https://www.triz.co.uk/learning-centre-innovation-tools (may require email signup)
- TRIZ Consulting Group PDF: https://www.triz-consulting.de/wp-content/uploads/2021/09/Contradiction_Matrix_V11.pdf
- Stan Kaplan document appendices: https://arvindvenkatadri.com/teaching/1-play-and-invent/modules/1000-triz-documents/TRIZ-related/Stan%20Kaplan-Intro-to-TRIZ.pdf
- Any additional GitHub repos found under the triz topic: https://github.com/topics/triz
- IKRA TRIZ Cards (Russian): https://ikraikra.ru/triz-cards
- InnovateTRIZ repo: https://github.com/ligj1706/InnovateTRIZ
- Roslyn-gh 40Principles repo: https://github.com/Roslyn-gh/40Principles
- trizchina Django repo: https://github.com/trizchina/triz
- IIT Bombay Excel: https://www.ee.iitb.ac.in/~apte/matrix.xls
- Designorate Excel: https://www.designorate.com/wp-content/uploads/2016/08/Designorate-TRIZ-Matrix.xls

If any of these yield extractable matrix data not already covered by Files 1-12, create additional numbered files following the same schema.

## Process — One File at a Time

For each file:

1. **Fetch** the source URL and extract raw data
2. **Parse** into the JSON schema above
3. **Save** as the specified filename
4. **Validate** using the validation process below
5. **Report** extraction statistics

**Do NOT proceed to the next file until the current file passes validation.**

## Validation Process (Critical — Do Not Skip)

After generating each JSON file, perform ALL of these validation steps:

### Step 1: Internal Consistency Check (automated)
Write and run a Python validation script that checks:
- Every principle ID referenced in any matrix cell exists in the principles object
- Every parameter ID used as a key in matrix (both outer and inner keys) exists in the parameters object
- No parameter maps to itself (no diagonal entries — improving X worsening X should not exist)
- No duplicate cells
- All principle IDs in cells are valid integers
- Matrix dimensions match what meta.dimensions claims
- All arrays in matrix cells are non-empty (no empty arrays — those cells should be omitted)
- Total populated cells count is reported

### Step 2: Source Cross-Verification (manual spot-check)
- Go back to the original source URL
- Pick 10 random populated matrix cells from the generated JSON
- For each cell, look up the same improving/worsening parameter pair in the source
- Verify the principle list matches EXACTLY (same principles, same order if order matters in source)
- Pick 5 random parameters and verify names match the source exactly
- Pick 3 random principles and verify names match the source
- Document verification results: "10/10 cells verified" or list specific discrepancies
- If ANY discrepancy is found: fix the file and re-run Step 1

### Step 3: Cross-Matrix Verification (after all 39x39 variants are complete)
After Files 1, 2, 8, 9, 10, and 11 are all generated, write a Python script that:
- Loads all 39x39 JSON files
- Compares every populated cell across all files
- Reports cells where different sources disagree on which principles are listed
- Reports parameters where names differ between sources
- Produces a discrepancy report

### Step 4: Statistics Report
For each completed and validated file, output:
```
Matrix: [filename]
Parameters: [count]
Principles defined: [count in principles object]
Principles actually referenced: [count unique principle IDs used across all matrix cells]
Principles never referenced: [list of IDs that exist in principles but never appear in matrix]
Total populated cells: [count]
Total possible cells: [N x (N-1)] excluding diagonal
Sparsity: [percentage of cells that are empty]
Most referenced principle: [ID, name, count of cells it appears in]
Least referenced principle: [ID, name, count of cells it appears in]
Average principles per populated cell: [number]
Max principles in a single cell: [number]
Min principles in a single cell: [number]
```

## Final Deliverables

After ALL files are generated and validated:

1. All JSON files in a /matrices/ folder
2. A validation_report.md documenting:
   - All spot-check results for every file
   - Cross-matrix discrepancy analysis
   - Any source URLs that were inaccessible or had incomplete data
3. A meta_analysis.md containing:
   - Side-by-side comparison table of all matrices (dimensions, sparsity, domain)
   - Principle frequency analysis across ALL matrices combined
   - Which principles appear in every matrix vs which are domain-specific
   - Which parameter pairs have the most consensus across different matrix versions
   - Any patterns in how domain-specific matrices modify or extend the classic
   - Assessment: is there a universal core subset of principles that covers 80%+ of all matrix cells across all domains?
   - Assessment: which parameters from different domains map to conceptually similar ideas?
