#!/usr/bin/env python3
"""validate_artifact.py — schema validator for run artifacts.

Two modes:

    validate_artifact.py <path>
        Direct mode. Exit 0 if valid; exit 1 if invalid; diagnostics on stdout.

    validate_artifact.py --hook-mode [<path>]
        Hook mode (design v6 §12). Always exits 0. Emits one JSON line per
        validation event to stdout (the plugin manifest redirects this to
        .triz/hook.log). The hook is a safety net; the actual halt point
        is the state-driver's pre-dispatch check.

The schema for an artifact is determined by filename pattern (see
_common.schema_for_artifact). Files we can't classify are reported as
'unknown_artifact' (skipped in hook mode, error in direct mode).

In hook mode the path may also come from the hook payload on stdin
(Claude Code's PostToolUse hook protocol). We accept both forms because
local testing is easier without faking the hook envelope.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import jsonschema

# Path bootstrap so we work whether invoked as a script or imported.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402


def _load_target(path_str: str) -> tuple[Path, dict | list | None, str | None]:
    """Read and JSON-parse the file at path. Returns (path, data, error)."""
    p = Path(path_str)
    if not p.exists():
        return p, None, f"file not found: {p}"
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return p, None, f"invalid JSON: {e}"
    except OSError as e:
        return p, None, f"read error: {e}"
    return p, data, None


def _validate(path: Path, data) -> tuple[bool, str, list[str]]:
    """Returns (ok, schema_filename_or_status, errors)."""
    schema_name = _common.schema_for_artifact(path.name)
    if schema_name is None:
        return False, "unknown_artifact", [
            f"no schema mapping for filename: {path.name}"
        ]
    try:
        schema = _common.load_schema(schema_name)
    except Exception as e:
        return False, schema_name, [f"failed to load schema: {e}"]
    validator = jsonschema.Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errs:
        return True, schema_name, []
    return False, schema_name, [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in errs
    ]


def _read_hook_payload_from_stdin() -> str | None:
    """Best-effort: extract a file path from a Claude Code hook payload on stdin.

    Returns None if stdin is a TTY or the payload doesn't contain a file_path.
    We never block on stdin: PostToolUse always feeds JSON; running locally
    without stdin is fine (hook mode just emits 'no_target').
    """
    if sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read()
    except Exception:
        return None
    if not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    # The PostToolUse payload nests tool_input under various shapes; try a few.
    for key_path in (
        ("tool_input", "file_path"),
        ("tool_input", "filePath"),
        ("tool_input", "path"),
        ("file_path",),
        ("path",),
    ):
        cur = payload
        ok = True
        for k in key_path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok and isinstance(cur, str):
            return cur
    return None


def _emit_hook_line(record: dict) -> None:
    record.setdefault("ts", time.time())
    sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_artifact.py",
        description="Validate a triz-workshop run artifact against its JSON schema.",
    )
    parser.add_argument(
        "path", nargs="?",
        help="Path to the artifact JSON file. In hook mode, may be omitted "
             "if the hook payload on stdin carries the path.",
    )
    parser.add_argument(
        "--hook-mode", action="store_true",
        help="Hook mode: always exit 0, emit one JSON line per validation.",
    )
    args = parser.parse_args(argv)

    path_str = args.path
    if args.hook_mode and not path_str:
        path_str = _read_hook_payload_from_stdin()

    if not path_str:
        if args.hook_mode:
            _emit_hook_line({"event": "no_target", "reason": "no path on argv or stdin"})
            return 0
        print("error: no path provided", file=sys.stderr)
        return 1

    # Only validate JSON files; the hook fires on every Write/Edit, including
    # markdown reports. Skip non-json silently in hook mode.
    if not path_str.endswith(".json"):
        if args.hook_mode:
            _emit_hook_line({"event": "skipped", "path": path_str, "reason": "not_json"})
            return 0
        print(f"skipped (not JSON): {path_str}")
        return 0

    p, data, load_err = _load_target(path_str)
    if load_err is not None:
        if args.hook_mode:
            _emit_hook_line({
                "event": "load_error",
                "path": str(p),
                "error": load_err,
            })
            return 0
        print(f"INVALID: {p}\n  {load_err}")
        return 1

    ok, schema_name, errs = _validate(p, data)

    if args.hook_mode:
        _emit_hook_line({
            "event": "validated" if ok else "invalid",
            "path": str(p),
            "schema": schema_name,
            "errors": errs,
        })
        return 0

    if ok:
        print(f"OK: {p} matches {schema_name}")
        return 0
    print(f"INVALID: {p} (schema: {schema_name})")
    for e in errs:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        # Never crash a hook. In direct mode, stderr+nonzero is fine.
        if "--hook-mode" in sys.argv:
            sys.stdout.write(json.dumps({
                "event": "internal_error",
                "error": f"{type(e).__name__}: {e}",
            }) + "\n")
            sys.exit(0)
        print(f"internal error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
