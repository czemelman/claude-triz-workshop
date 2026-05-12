# Licenses

The plugin itself is MIT (see `triz-workshop/LICENSE`).

The matrix corpus is a mosaic of independently-licensed sources. The table below documents each matrix's license, whether it ships bundled in this repo, and the attribution required.

## Bundled matrices

| Matrix ID | License | Source | Attribution required |
|---|---|---|---|
| `altshuller_39x39` | Public domain | triz40.com extraction of Altshuller 1971 | No |
| `altshuller_russian_original` | Public domain | Russian-language original of Altshuller 1971 | No |
| `biotriz_6x6_bio` | CC BY 4.0 | Vincent, Mann, Bogatyreva (2006), PMC1664643 — biology submatrix | Yes (see below) |
| `biotriz_6x6_tech` | CC BY 4.0 | Vincent, Mann, Bogatyreva (2006), PMC1664643 — technology submatrix | Yes (see below) |
| `biotriz_24x24` | CC BY 4.0 (PMC Open Access) | Vincent, Mann, Bogatyreva (2006), expanded version | Yes (see below) |
| `healthcare_servqual` | CC BY 4.0 | Lee, Lee, Chiang, et al. (2024), Nature Scientific Reports, DOI 10.1038/s41598-024-78661-3 | Yes (see below) |
| `heinrich_39x39` | Apache-2.0 | Heinrich "The Inventing Machine" curated subset | Yes (NOTICE preserved) |
| `innovatetriz_extended` | MIT | InnovateTRIZ bilingual extension | Yes |
| `triz_ai_50x50` | MIT | LLM-curated 50-parameter extension | Yes |

## Attribution lines

### BioTRIZ matrices (CC BY 4.0)

> Vincent, J. F. V., Bogatyreva, O. A., Bogatyrev, N. R., Bowyer, A., & Pahl, A.-K. (2006). Biomimetics: its practice and theory. *Journal of the Royal Society Interface*, 3(9), 471-482. PMC1664643. Used under Creative Commons Attribution 4.0 International License.

### Healthcare SERVQUAL matrix (CC BY 4.0)

> Lee, J.-Y., Lee, P.-S., Chiang, C.-H., Chen, Y.-P., Chen, C.-J., Huang, Y.-M., Chiu, J.-R., Yang, P.-C., Yeh, C.-A., & Chang, J.-T. (2024). [SERVQUAL TRIZ contradiction matrix for healthcare service quality]. *Scientific Reports*, 14, [article]. DOI: 10.1038/s41598-024-78661-3. Used under Creative Commons Attribution 4.0 International License.

### Heinrich matrix (Apache-2.0)

> Heinrich, J. (n.d.). The Inventing Machine — TRIZ contradiction matrix curated subset. Licensed under Apache License 2.0.

### InnovateTRIZ (MIT)

> InnovateTRIZ Extended Contradiction Matrix. Licensed under MIT.

## NOT bundled (restricted-license matrices)

These matrices exist in the design and the registry but are NOT shipped in this repo. Plugin users can fetch them from source if they want them — see `MATRICES_OPTIONAL.md`.

| Matrix ID | License | Reason not bundled |
|---|---|---|
| `drug_safety_18x18` | CC BY-NC-ND 4.0 | NonCommercial + NoDerivatives — redistribution in an MIT-licensed plugin is a license violation. |
| `mann_matrix2003_48x48` | "Used with permission for educational/research purposes" | Explicitly not redistributable. Also a shell file (zero populated cells), so no functional loss for the plugin. |

## Plugin code license

All Python scripts, JSON schemas, subagent prompts, slash command bodies, methodology skill, tests, eval harness, and design documents in this repo are released under the MIT License (see `triz-workshop/LICENSE`).

## Provenance copies

The files in `matrices/redundant/` (matriz_org_39x39, triz_agents_39x39, biotriz_6x6_legacy) are duplicate snapshots preserved for cell-hash verification. They carry the same license as their canonical equivalents.
