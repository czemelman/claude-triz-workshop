"""Shared utilities for the triz-workshop deterministic scripts.

This module is the single source of truth for:
- Filesystem layout of run artifacts under .triz/runs/<run_id>/
- Resolving and loading the matrix corpus (registry + matrix files + use cases)
- Atomic JSON IO (write-then-rename, never partial files visible)
- Canonical Stage and Decision enums consumed by select_matrix.py and next_action.py

All other scripts import from here. Direct filesystem or env access elsewhere
is a smell.
"""

from __future__ import annotations

import enum
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


# --- Path resolution -------------------------------------------------------

# Plugin root: the directory containing scripts/, schemas/, .claude-plugin/.
# Scripts are designed to be invoked from the user's working directory (CWD),
# so .triz/runs/ is rooted at CWD, not at the plugin root.
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def plugin_root() -> Path:
    return _PLUGIN_ROOT


def matrices_root() -> Path:
    """Resolve the matrix corpus root.

    Precedence (matches design v6 §23):
        1. TRIZ_MATRICES_PATH env var
        2. ./Triz_matrixes relative to plugin root's parent
           (the way this repo is laid out: matrices live as a sibling of the
           plugin, not inside it)
    """
    env = os.environ.get("TRIZ_MATRICES_PATH")
    if env:
        p = Path(env).expanduser().resolve()
        if p.exists():
            return p
        # If env was set but doesn't resolve, fall back to default to keep
        # tests / smoke runs working even when the env points at nothing.
    # Default: corpus is a sibling of the plugin (this repo's layout).
    candidate = _PLUGIN_ROOT.parent
    if (candidate / "registry.json").exists():
        return candidate
    # Last-resort: a Triz_matrixes subdir under the plugin's parent.
    return (_PLUGIN_ROOT.parent / "Triz_matrixes").resolve()


def schemas_root() -> Path:
    return _PLUGIN_ROOT / "schemas"


def triz_state_root() -> Path:
    """Where .triz/runs/ lives. Rooted at the user's CWD."""
    return Path(os.getcwd()) / ".triz"


# --- Run directory + artifact IO ------------------------------------------

def run_dir(run_id: str, create: bool = True) -> Path:
    """Absolute path to .triz/runs/<run_id>/.

    Creates the directory (and parents) when `create=True`. Used by both
    new-run initialization and existing-run lookups.
    """
    if not run_id or "/" in run_id or ".." in run_id:
        raise ValueError(f"invalid run_id: {run_id!r}")
    rd = triz_state_root() / "runs" / run_id
    if create:
        rd.mkdir(parents=True, exist_ok=True)
    return rd


def atomic_write(path: Path | str, data: Any) -> None:
    """Write JSON atomically: tmp file in the same dir, fsync, rename.

    Same-directory tmp guarantees rename is atomic on POSIX (no cross-device
    move). Hook log readers and concurrent state-driver invocations never see
    a half-written file.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Encode first so we don't create a tmp file when the data is bad.
    if isinstance(data, (dict, list)):
        text = json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False)
    elif isinstance(data, str):
        text = data
    else:
        text = json.dumps(data, indent=2, ensure_ascii=False)
    fd, tmp_path = tempfile.mkstemp(
        prefix=p.name + ".", suffix=".tmp", dir=str(p.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, p)
    except Exception:
        # Best-effort cleanup of leftover tmp file.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def read_artifact(run_id: str, name: str) -> dict | list:
    p = run_dir(run_id, create=False) / name
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_artifact(run_id: str, name: str, data: Any) -> Path:
    p = run_dir(run_id) / name
    atomic_write(p, data)
    return p


def artifact_exists(run_id: str, name: str) -> bool:
    return (run_dir(run_id, create=False) / name).exists()


def list_artifacts(run_id: str, glob: str = "*.json") -> list[Path]:
    rd = run_dir(run_id, create=False)
    if not rd.exists():
        return []
    return sorted(rd.glob(glob))


# --- Registry / matrix / use-case loaders ---------------------------------

# In-process cache keyed by absolute file path. The corpus does not change
# during a single process's lifetime; reloading on every call wastes IO.
_LOAD_CACHE: dict[str, Any] = {}


def _load_json(path: Path) -> Any:
    key = str(path)
    if key in _LOAD_CACHE:
        return _LOAD_CACHE[key]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _LOAD_CACHE[key] = data
    return data


def load_registry() -> dict:
    p = matrices_root() / "registry.json"
    return _load_json(p)


def _registry_entry(matrix_id: str) -> dict:
    reg = load_registry()
    for m in reg.get("matrices", []):
        if m.get("id") == matrix_id:
            return m
    raise KeyError(f"matrix_id not in registry: {matrix_id!r}")


def load_matrix(matrix_id: str) -> dict:
    entry = _registry_entry(matrix_id)
    rel = entry.get("matrix_file")
    if not rel:
        raise KeyError(f"registry entry for {matrix_id!r} has no matrix_file")
    return _load_json(matrices_root() / rel)


def load_use_case(matrix_id: str) -> dict:
    entry = _registry_entry(matrix_id)
    rel = entry.get("use_case_file")
    if not rel:
        # Some redundant entries have no use case; that's allowed.
        return {}
    p = matrices_root() / rel
    if not p.exists():
        return {}
    return _load_json(p)


def load_vocabulary() -> dict:
    p = matrices_root() / "selector_tags_vocabulary.json"
    return _load_json(p)


# --- Hashing ---------------------------------------------------------------

def compute_cell_hash(matrix_dict: dict) -> str:
    """SHA-256 of the canonical-JSON form. Used for replay snapshot integrity."""
    canon = json.dumps(matrix_dict, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()


# --- Stage + Decision enums -----------------------------------------------

class Stage(enum.Enum):
    """The 17 critical-path stages from design v6 §20.5."""
    INIT = "init"
    FRAMER = "framer"
    CHECK_FRAMING_CONFIDENCE = "check_framing_confidence"
    SELECT_MATRIX = "select_matrix"
    STAGE_E_CHECK = "stage_e_check"
    MAPPING_PHASE1 = "mapping_phase1"
    COMPARE_MAPPINGS = "compare_mappings"
    MAPPING_PHASE2 = "mapping_phase2"
    LOOKUP = "lookup"
    INTERPRET = "interpret"
    MERGE_INTERPRETATIONS = "merge_interpretations"
    SYNTHESIZE = "synthesize"
    CRITIQUE = "critique"
    CHECK_FATAL_SEVERITY = "check_fatal_severity"
    ASSEMBLE = "assemble"
    DONE = "done"


class Decision(enum.Enum):
    """Returns of compare_mappings() per design v6 §15.2."""
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    NO_CLEAN_MAPPING = "NO_CLEAN_MAPPING"


# --- Schema loading -------------------------------------------------------

def load_schema(schema_filename: str) -> dict:
    return _load_json(schemas_root() / schema_filename)


# Map from artifact filename pattern to schema file. Lookup order matters
# because some patterns are prefixes of others (03_mapping_X vs 03b_X).
_ARTIFACT_TO_SCHEMA: list[tuple[str, str]] = [
    ("01_problem", "01_problem.schema.json"),
    ("02_selection", "02_selection.schema.json"),
    ("03b_mapping_critique", "03b_mapping_critique.schema.json"),
    ("03c_independent_mapping", "03c_independent_mapping.schema.json"),
    ("03_mapping", "03_mapping.schema.json"),
    ("04_principles", "04_principles.schema.json"),
    ("05_interpretation_", "05_interpretation_single.schema.json"),
    ("05_interpretations", "05_interpretations.schema.json"),
    ("06_solutions", "06_solutions.schema.json"),
    ("07_critique", "07_critique.schema.json"),
    ("selector_tags_vocabulary", "selector_tags_vocabulary.schema.json"),
]


def schema_for_artifact(filename: str) -> str | None:
    """Return the schema filename for a given artifact basename, or None."""
    base = Path(filename).name
    # 05_interpretations.json must take precedence over 05_interpretation_ (the
    # per-principle artifact is `05_interpretation_<m>_<p>.json`). Explicit
    # check for the merged file is clearer than juggling pattern order.
    if base.startswith("05_interpretations"):
        return "05_interpretations.schema.json"
    for prefix, schema in _ARTIFACT_TO_SCHEMA:
        if base.startswith(prefix):
            return schema
    return None
