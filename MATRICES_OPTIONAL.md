# Optional matrices (not bundled)

Two matrices in the design are NOT shipped in this repo due to license restrictions. The plugin works without them. If you want them, you fetch them yourself and drop the JSON file into `matrices/`.

## `drug_safety_18x18`

**License:** CC BY-NC-ND 4.0 (NonCommercial + NoDerivatives) — incompatible with this MIT-licensed plugin's redistribution. You can use it personally for your own analyses, but I can't ship it.

**Source:** *The drug safety governance contradiction matrix* — see the paper from which the parameters and cells were extracted. (Search "drug safety TRIZ governance matrix" or contact the author.)

**Use cases:** Multi-stakeholder pharmaceutical governance, regulatory tension resolution, public-trust-vs-enforcement trade-offs.

**To install locally:**
1. Obtain the matrix data from the original source.
2. Format it as a v6-compliant matrix file (see `matrix_storage_design.md` §3 + amendments). Helpful reference: any of the bundled matrix files.
3. Save to `matrices/drug_safety_18x18.json`.
4. Run `python3 validate_matrix.py --strict matrices/drug_safety_18x18.json`.
5. Run `python3 scripts/regenerate_registry.py` to refresh `registry.json`.

The use-case file (`use_cases/drug_safety_18x18.json`) is shipped — it describes when the matrix should be selected. Once you drop the matrix file in place, the plugin will route governance problems to it automatically.

## `mann_matrix2003_48x48`

**License:** "Used with permission for educational/research purposes" — explicitly NOT redistributable.

**Source:** Mann, D. (2003). *Hands-On Systematic Innovation*. The 48-parameter Matrix 2003 was published as a poster (PDF available at `arvindvenkatadri.com/pdf/TRIZ/ContradictionMatrix2003.pdf`); cells require manual extraction from the visual layout.

**Note:** This matrix is shell-only in the design — it carries the 48-parameter taxonomy but has zero populated cells (extraction never completed). It's marked `status: "shell"` in the registry. Even if you fetch it, the plugin's Stage A filter drops shell matrices unless `--matrix=mann_matrix2003_48x48` is explicitly requested.

**To install locally:**
Same procedure as drug_safety above. The use-case file is shipped.
