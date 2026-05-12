# triz-workshop

A Claude Code plugin that turns a TRIZ matrix collection into a working
contradiction-resolution pipeline.

## Status

Phase 1 scaffold (v0.1.0). See `triz_workshop_design.md` (v6) at the project
root for the full design.

## What it does

Given a contradiction expressed as `improving X / worsening Y`, the plugin:

1. Frames the problem (signals, contradiction type, domain class).
2. Selects the most appropriate matrix (or matrices) from the registry via a
   five-stage scoring algorithm.
3. Maps the problem to parameters (with an independent mapping critic).
4. Looks up principles in the cell.
5. Interprets each principle for the user's domain (lineage-aware: Altshuller,
   BioTRIZ, drug-safety, TRIZ-AI).
6. Synthesizes 1-4 ranked solution candidates.
7. Critiques those candidates for secondary contradictions and severity.

Every step writes a numbered JSON artifact to `.triz/runs/<run-id>/`. The run
is replayable, diff-able, reviewable.

## Slash commands

- `/triz-workshop:triz-solve "<problem>"` - end-to-end pipeline.
- `/triz-workshop:triz-list-matrices` - list available matrices in the registry.
- `/triz-workshop:triz-explain-matrix <id>` - print a matrix card.
- `/triz-workshop:triz-replay <run-id>` - replay a previous run.

## Caveats

- The TRIZ contradiction-matrix methodology has a ~10-15% clean-mapping rate
  on real-world problems (per Souchkov). Unmappable problems are a normal
  output state, not an error.
- Selection weights are tagged `weights_version: "v0"` (uncalibrated) until
  an eval set produces calibrated `v1` weights.
- v0.1 is English-only; non-English matrices ship in v1.0+.

## Configuration

- Environment: `TRIZ_MATRICES_PATH` points at the matrix collection root.
- Project config: `.triz/config.json` (see design doc S23).

## License

MIT (placeholder; see `LICENSE`).
