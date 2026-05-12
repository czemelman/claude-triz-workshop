#!/usr/bin/env python3
"""merge_interpretations.py — consolidate per-principle interpretation files.

Per design v6 §10.4 + §13:
- Reads every 05_interpretation_<m>_<p>.json in the run dir.
- Sorts by (principle_canonical_id, interpretation_lineage). Sorting at
  this layer (not at the synthesizer) is what makes the merged artifact
  diff-stable across replays.
- Does NOT dedup. Two interpretations sharing canonical_id but differing
  in interpretation_lineage are distinct cross-matrix angles (§9.6a).
- Moves the consumed per-principle files into partial/ so they remain
  available for replay but don't clutter the top-level artifact list.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jsonschema

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402


def merge(run_id: str) -> dict:
    rd = _common.run_dir(run_id, create=False)
    if not rd.exists():
        raise FileNotFoundError(f"run dir not found: {rd}")

    # The merged file uses the prefix `05_interpretations.json` (no underscore
    # after `interpretations`). The per-principle files are
    # `05_interpretation_<matrix>_<principle>.json` (singular, with two _).
    # Glob carefully so we don't pick up the merged file itself on a re-run.
    candidates = sorted(rd.glob("05_interpretation_*.json"))
    interpretations: list[dict] = []
    sources: list[Path] = []
    for p in candidates:
        # Defensive: skip the merged file in case the prefix glob ever matches.
        if p.name.startswith("05_interpretations"):
            continue
        try:
            data = _common.read_artifact(run_id, p.name)
        except Exception as e:
            print(f"merge_interpretations: skipping {p.name}: {e}",
                  file=sys.stderr)
            continue
        # Strip schema_version when packing into the merged array; the merged
        # schema only requires the per-entry data fields.
        entry = {k: v for k, v in data.items() if k != "schema_version"}
        interpretations.append(entry)
        sources.append(p)

    interpretations.sort(key=lambda e: (
        e.get("principle_canonical_id", ""),
        e.get("interpretation_lineage", ""),
        e.get("matrix_id", ""),
        e.get("principle_id", ""),
    ))

    return {
        "schema_version": 1,
        "interpretations": interpretations,
    }, sources


def _validate(out: dict) -> None:
    schema = _common.load_schema("05_interpretations.schema.json")
    jsonschema.Draft202012Validator(schema).validate(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="merge_interpretations.py",
        description="Merge 05_interpretation_*.json files into 05_interpretations.json. "
                    "Sorted by (canonical_id, interpretation_lineage); not deduped.",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--keep-sources", action="store_true",
        help="Don't move per-principle files into partial/; useful for tests.",
    )
    args = parser.parse_args(argv)

    try:
        merged, sources = merge(args.run_id)
    except FileNotFoundError as e:
        print(f"merge_interpretations: {e}", file=sys.stderr)
        return 2

    if not merged["interpretations"]:
        print(
            f"merge_interpretations: no 05_interpretation_*.json files in run dir.",
            file=sys.stderr,
        )
        # Still write the (empty-array) artifact: schema allows empty array.
        # Downstream synthesizer will see no input and itself escalate.

    try:
        _validate(merged)
    except jsonschema.ValidationError as e:
        print(f"merge_interpretations: schema validation failed: {e.message}",
              file=sys.stderr)
        return 3

    out_path = _common.write_artifact(args.run_id, "05_interpretations.json", merged)

    moved = 0
    if not args.keep_sources and sources:
        partial = _common.run_dir(args.run_id) / "partial"
        partial.mkdir(parents=True, exist_ok=True)
        for src in sources:
            try:
                src.replace(partial / src.name)
                moved += 1
            except OSError as e:
                print(
                    f"merge_interpretations: failed to move {src.name} to partial/: {e}",
                    file=sys.stderr,
                )

    print(
        f"merge_interpretations: wrote {out_path} "
        f"(entries={len(merged['interpretations'])}, sources_moved={moved})"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"merge_interpretations: internal error: {type(e).__name__}: {e}",
              file=sys.stderr)
        sys.exit(2)
