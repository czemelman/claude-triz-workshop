#!/usr/bin/env python3
"""lookup_principles.py — read a matrix cell + alternatives, write 04_principles_<m>.json.

Per design v6 §10.3a:
- meta.diagonal_cells == "excluded" + mapper i==j  → return populated:false immediately
  (the state-driver branches to no-clean-mapping).
- meta.parameter_id_style == "prefixed" → keys are passed verbatim, NO int coercion.
- If primary cell is empty, try each alternatives[] full pair in order.
- Record every attempt in alternatives_tried[] for replay reproducibility.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402


def _normalize_key(key: str, style: str) -> str:
    """Parameter-id key normalization.

    For numeric matrices, ids in the matrix dict are stringified ints
    ("1".."39"). The mapper is required to emit strings via schema; we
    normalize whitespace but otherwise keep the value as-is.

    For 'prefixed' (S1/T19), values are kept verbatim including case.
    For 'alphanumeric' (innovatetriz), same treatment as prefixed.
    """
    k = (key or "").strip()
    return k


def _try_cell(matrix: dict, improving: str, worsening: str) -> tuple[bool, list[int]]:
    cells = matrix.get("matrix") or {}
    row = cells.get(improving)
    if not isinstance(row, dict):
        return False, []
    cell = row.get(worsening)
    if cell is None:
        return False, []
    if isinstance(cell, list):
        # Cells can carry stringified ints in some sources; coerce defensively.
        principles: list[int] = []
        for p in cell:
            try:
                principles.append(int(p))
            except (TypeError, ValueError):
                continue
        if not principles:
            # Empty list = explicitly "no principles for this cell".
            return False, []
        return True, principles
    return False, []


def lookup(matrix_id: str, mapping: dict) -> dict:
    matrix = _common.load_matrix(matrix_id)
    meta = matrix.get("meta") or {}
    style = meta.get("parameter_id_style", "numeric")
    diag = meta.get("diagonal_cells", "excluded")

    primary_imp = _normalize_key(mapping["improving_param_id"], style)
    primary_wor = _normalize_key(mapping["worsening_param_id"], style)
    alternatives = mapping.get("alternatives") or []

    attempts: list[dict] = []

    # Diagonal-excluded short circuit. The state-driver should already have
    # caught this, but defensive: a mapper that emits i==j on a diagonal-
    # excluded matrix gets an immediate empty result.
    if diag == "excluded" and primary_imp == primary_wor:
        attempts.append({
            "improving_param_id": primary_imp,
            "worsening_param_id": primary_wor,
            "found": False,
            "skipped_reason": "diagonal cell excluded by matrix meta",
        })
        return {
            "schema_version": 1,
            "matrix_id": matrix_id,
            "populated": False,
            "principles": [],
            "alternatives_tried": attempts,
        }

    # Primary cell.
    ok, principles = _try_cell(matrix, primary_imp, primary_wor)
    attempts.append({
        "improving_param_id": primary_imp,
        "worsening_param_id": primary_wor,
        "found": ok,
        "principles": principles if ok else [],
    })
    if ok:
        return {
            "schema_version": 1,
            "matrix_id": matrix_id,
            "populated": True,
            "principles": principles,
            "alternatives_tried": attempts,
        }

    # Alternatives in order. First hit wins; remaining entries are recorded
    # but not consulted (replay can reproduce by re-walking).
    for alt in alternatives:
        ai = _normalize_key(alt.get("improving_param_id", ""), style)
        aw = _normalize_key(alt.get("worsening_param_id", ""), style)
        if diag == "excluded" and ai == aw:
            attempts.append({
                "improving_param_id": ai,
                "worsening_param_id": aw,
                "found": False,
                "skipped_reason": "diagonal cell excluded by matrix meta",
            })
            continue
        ok, principles = _try_cell(matrix, ai, aw)
        attempts.append({
            "improving_param_id": ai,
            "worsening_param_id": aw,
            "found": ok,
            "principles": principles if ok else [],
        })
        if ok:
            return {
                "schema_version": 1,
                "matrix_id": matrix_id,
                "populated": True,
                "principles": principles,
                "alternatives_tried": attempts,
            }

    # Nothing populated. State-driver branches to no-clean-mapping.
    return {
        "schema_version": 1,
        "matrix_id": matrix_id,
        "populated": False,
        "principles": [],
        "alternatives_tried": attempts,
    }


def _validate(out: dict) -> None:
    schema = _common.load_schema("04_principles.schema.json")
    jsonschema.Draft202012Validator(schema).validate(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lookup_principles.py",
        description="Look up principles for a (mapper) cell + alternatives. "
                    "Writes 04_principles_<matrix>.json.",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--matrix", required=True,
                        help="Matrix id; reads 03_mapping_<matrix>.json from the run dir.")
    args = parser.parse_args(argv)

    mapping_filename = f"03_mapping_{args.matrix}.json"
    try:
        mapping = _common.read_artifact(args.run_id, mapping_filename)
    except FileNotFoundError:
        print(
            f"lookup_principles: {mapping_filename} not found for run {args.run_id}.",
            file=sys.stderr,
        )
        return 2

    if mapping.get("matrix_id") != args.matrix:
        print(
            f"lookup_principles: mapping artifact's matrix_id "
            f"({mapping.get('matrix_id')!r}) does not match --matrix "
            f"({args.matrix!r}).",
            file=sys.stderr,
        )
        return 3

    try:
        result = lookup(args.matrix, mapping)
    except KeyError as e:
        print(f"lookup_principles: matrix not in registry: {e}",
              file=sys.stderr)
        return 4
    except Exception as e:
        print(f"lookup_principles: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 5

    try:
        _validate(result)
    except jsonschema.ValidationError as e:
        print(f"lookup_principles: result failed schema validation: {e.message}",
              file=sys.stderr)
        return 6

    out_name = f"04_principles_{args.matrix}.json"
    out = _common.write_artifact(args.run_id, out_name, result)
    print(f"lookup_principles: wrote {out} "
          f"(populated={result['populated']}, "
          f"principles={result['principles']}, "
          f"attempts={len(result['alternatives_tried'])})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"lookup_principles: internal error: {type(e).__name__}: {e}",
              file=sys.stderr)
        sys.exit(2)
