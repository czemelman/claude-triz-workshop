#!/usr/bin/env python3
"""compatibility_check.py — verifies the matrix corpus's storage schema
matches what this plugin can read.

Per design v6 §22 (failure-modes table) and §24 (versioning), the plugin
declares a `compatibility.matrix_collection_schema` semver range in its
`plugin.json`. The registry declares its own `schema_version`. If the
registry's version is outside the plugin's range, every downstream
operation is unsafe and we halt before any pipeline work begins.

Invoked once per session by `next_action.py` on first invocation.

Exit 0 = compatible. Non-zero + actionable error = incompatible or
corpus unreadable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402


# --- Minimal semver range parser ------------------------------------------
# We intentionally don't depend on a third-party semver library. The plugin's
# `compatibility.matrix_collection_schema` uses a small subset of npm-style
# range syntax: e.g. ">=1.1.0 <2.0.0". A handwritten parser keeps the install
# footprint to jsonschema only.

_RANGE_RE = re.compile(r"\s*(>=|<=|>|<|=)\s*([0-9]+(?:\.[0-9]+){0,2})")


def _normalize_version(v: str) -> tuple[int, int, int]:
    parts = (v.strip().split(".") + ["0", "0", "0"])[:3]
    try:
        return tuple(int(x) for x in parts)  # type: ignore[return-value]
    except ValueError as exc:
        raise ValueError(f"not a numeric semver: {v!r}") from exc


def _cmp_version(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return (a > b) - (a < b)


def in_range(version: str, range_expr: str) -> bool:
    v = _normalize_version(version)
    constraints = _RANGE_RE.findall(range_expr)
    if not constraints:
        raise ValueError(f"unparseable range: {range_expr!r}")
    for op, ref in constraints:
        rv = _normalize_version(ref)
        c = _cmp_version(v, rv)
        if op == ">=" and c < 0:
            return False
        if op == ">" and c <= 0:
            return False
        if op == "<=" and c > 0:
            return False
        if op == "<" and c >= 0:
            return False
        if op == "=" and c != 0:
            return False
    return True


def _load_plugin_manifest() -> dict:
    p = _common.plugin_root() / ".claude-plugin" / "plugin.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="compatibility_check.py",
        description="Verify the matrix corpus's schema_version is within the "
                    "plugin's supported range.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress success output; only print on failure.",
    )
    args = parser.parse_args(argv)

    try:
        manifest = _load_plugin_manifest()
    except Exception as e:
        print(
            f"compatibility_check: failed to load plugin manifest: {e}\n"
            f"  Looked in: {_common.plugin_root() / '.claude-plugin' / 'plugin.json'}",
            file=sys.stderr,
        )
        return 2

    range_expr = manifest.get("compatibility", {}).get("matrix_collection_schema")
    if not range_expr:
        print(
            "compatibility_check: plugin manifest missing "
            "compatibility.matrix_collection_schema.",
            file=sys.stderr,
        )
        return 2

    try:
        registry = _common.load_registry()
    except FileNotFoundError as e:
        print(
            f"compatibility_check: registry not found.\n"
            f"  Set TRIZ_MATRICES_PATH or place registry.json at: "
            f"{_common.matrices_root()}\n"
            f"  Underlying error: {e}",
            file=sys.stderr,
        )
        return 3
    except Exception as e:
        print(
            f"compatibility_check: failed to load registry: {e}",
            file=sys.stderr,
        )
        return 3

    reg_version = str(registry.get("schema_version") or "")
    if not reg_version:
        print(
            "compatibility_check: registry has no schema_version field.",
            file=sys.stderr,
        )
        return 4

    try:
        ok = in_range(reg_version, range_expr)
    except ValueError as e:
        print(
            f"compatibility_check: cannot compare versions: {e}\n"
            f"  registry schema_version = {reg_version!r}\n"
            f"  plugin range            = {range_expr!r}",
            file=sys.stderr,
        )
        return 5

    if not ok:
        print(
            f"compatibility_check: registry schema_version {reg_version!r} is "
            f"OUTSIDE the plugin's supported range {range_expr!r}.\n"
            f"  Action: upgrade the plugin, or point TRIZ_MATRICES_PATH at a "
            f"corpus matching the supported range.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"compatibility_check: OK "
            f"(registry schema_version {reg_version} in {range_expr})"
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"compatibility_check: internal error: {type(e).__name__}: {e}",
              file=sys.stderr)
        sys.exit(2)
