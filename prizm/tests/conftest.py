"""Shared pytest fixtures for the prizm test suite.

Layout assumptions:
    prizm/
        scripts/next_action.py         — the state driver under test
        scripts/_common.py             — module imported by tests
        tests/
            conftest.py                — this file
            unit/                      — direct-import unit tests
            integration/               — subprocess fixture-driven tests
            fixtures/states/<NN>_*/    — state fixtures (B7 §7.3)
            fixtures/decisions/<dN>_*/ — decision fixtures
            property/                  — property-based tests

The plugin root (.../prizm) is auto-added to sys.path so unit tests
can `from scripts.next_action import _compare_mappings` without the user
having to install the plugin as a package.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# --- Root resolution & sys.path wiring ------------------------------------

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
TESTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
LIVE_MATRICES_PATH = PLUGIN_ROOT.parent  # registry.json sits at project root.

# Make `scripts.<module>` and `_common` importable from anywhere.
for p in (str(PLUGIN_ROOT), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)


# --- Path/env fixtures ----------------------------------------------------

@pytest.fixture(scope="session")
def plugin_root() -> Path:
    return PLUGIN_ROOT


@pytest.fixture(scope="session")
def scripts_dir() -> Path:
    return SCRIPTS_DIR


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def live_matrices_path() -> Path:
    """Project's matrix corpus root (where registry.json lives)."""
    return LIVE_MATRICES_PATH


# --- Per-test isolated run directory --------------------------------------

@pytest.fixture
def tmp_run_dir(tmp_path: Path) -> tuple[Path, str, Path]:
    """Create an isolated `<tmp>/.triz/runs/<run_id>/` directory.

    Returns (cwd, run_id, run_path) where:
        cwd        — what to pass as the subprocess `cwd` so .triz/ resolves there.
        run_id     — short deterministic id usable in CLI args.
        run_path   — the actual run dir on disk.
    """
    run_id = "test-run-" + tmp_path.name[-8:].replace(".", "-")
    run_path = tmp_path / ".triz" / "runs" / run_id
    run_path.mkdir(parents=True, exist_ok=True)
    return tmp_path, run_id, run_path


# --- Fixture loader -------------------------------------------------------

def copy_fixture_state(fixture_state_dir: Path, dest_run_dir: Path) -> None:
    """Copy every artifact under fixture_state_dir/ into dest_run_dir/.

    Skips manifest.json (present only for human readers; not consumed by the
    state driver). state.json IS copied — it carries current_stage and the
    flags the driver reads.
    """
    if not fixture_state_dir.exists():
        raise FileNotFoundError(f"missing fixture state/ at {fixture_state_dir}")
    for src in sorted(fixture_state_dir.iterdir()):
        if src.name == "manifest.json":
            continue
        if src.is_file():
            shutil.copy(src, dest_run_dir / src.name)


def install_fixture(fixture_dir: Path, tmp_path: Path) -> tuple[Path, str, dict]:
    """Materialize a fixture under tmp_path/.triz/runs/<run_id>/.

    Reads the fixture's invocation.json to determine the run-id (from
    invocation.args[1] when args[0] == "--run-id"), copies state files,
    and returns (cwd, run_id, invocation_dict).
    """
    inv_path = fixture_dir / "invocation.json"
    if not inv_path.exists():
        raise FileNotFoundError(f"missing invocation.json at {inv_path}")
    invocation = json.loads(inv_path.read_text(encoding="utf-8"))
    args = invocation.get("args") or []
    run_id = None
    for i, a in enumerate(args):
        if a == "--run-id" and i + 1 < len(args):
            run_id = args[i + 1]
            break
        if a.startswith("--run-id="):
            run_id = a.split("=", 1)[1]
            break
    if run_id is None and "--new-run" in args:
        # init fixture: no run yet; the driver generates the id.
        run_id = "<new>"
    if run_id is None:
        raise ValueError(f"could not extract run_id from invocation.json args: {args}")
    run_path = tmp_path / ".triz" / "runs" / run_id
    if run_id != "<new>":
        run_path.mkdir(parents=True, exist_ok=True)
        copy_fixture_state(fixture_dir / "state", run_path)
    return tmp_path, run_id, invocation


# --- Subprocess runner with strict CLI contract assertions ----------------

def subprocess_run_next_action(
    *cli_args: str,
    cwd: Path,
    env: dict | None = None,
    timeout: float = 30.0,
) -> dict:
    """Run next_action.py and assert the strict CLI contract per design v6 §19.2.

    Asserts: exit code == 0, stderr empty, stdout is one valid JSON object.
    Returns the parsed action dict.

    Subprocess-coverage wiring (B10):
        We export PYTHONPATH=<plugin_root> so the child Python process imports
        the in-tree `sitecustomize.py`, and we propagate COVERAGE_PROCESS_START
        if it is already set in the parent (CI sets it to .coveragerc) or
        default it to the plugin-local .coveragerc when that file exists.
        This causes coverage.process_startup() to fire in every child, writing
        per-pid .coverage.<pid>.<host> data files that `coverage combine`
        merges. With this in place, the 90% line-coverage gate on
        next_action.py (§20.9) can actually be evaluated; without it,
        subprocess-driven tests would not report any of the lines they hit.
    """
    script = SCRIPTS_DIR / "next_action.py"
    full_env = os.environ.copy()
    full_env.setdefault(
        "TRIZ_MATRICES_PATH", str(LIVE_MATRICES_PATH)
    )
    # Make sitecustomize.py reachable in the child interpreter. We prepend so
    # the in-tree sitecustomize wins over any system one.
    existing_pp = full_env.get("PYTHONPATH", "")
    parts = [str(PLUGIN_ROOT)]
    if existing_pp:
        parts.append(existing_pp)
    full_env["PYTHONPATH"] = os.pathsep.join(parts)
    # If parent didn't already point at a coverage config, default to the
    # plugin-local one. process_startup() is a no-op if coverage isn't
    # installed, so non-coverage runs are unaffected.
    if "COVERAGE_PROCESS_START" not in full_env:
        cov_cfg = PLUGIN_ROOT / ".coveragerc"
        if cov_cfg.exists():
            full_env["COVERAGE_PROCESS_START"] = str(cov_cfg)
    # Subprocesses run with cwd=tmp_path, but the coverage `data_file` setting
    # in .coveragerc is relative — without intervention every subprocess would
    # write its .coverage.<pid>.<host> into its own tmp_path and `coverage
    # combine` (run from the plugin root) would never find them. Force an
    # absolute COVERAGE_FILE so every subprocess writes into the plugin root.
    if "COVERAGE_PROCESS_START" in full_env and "COVERAGE_FILE" not in full_env:
        full_env["COVERAGE_FILE"] = str(PLUGIN_ROOT / ".coverage")
    if env:
        full_env.update(env)
    proc = subprocess.run(
        [sys.executable, str(script), *cli_args],
        cwd=str(cwd),
        env=full_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    assert proc.returncode == 0, (
        f"next_action.py exited {proc.returncode} (contract: must be 0). "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert proc.stderr == "", (
        f"next_action.py wrote stderr (contract: must be empty): {proc.stderr!r}"
    )
    stdout = proc.stdout.strip()
    assert stdout, "next_action.py produced no stdout"
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"next_action.py stdout is not valid JSON: {e}\nstdout={stdout!r}"
        )


@pytest.fixture
def run_next_action():
    """Pytest-friendly handle around subprocess_run_next_action."""
    return subprocess_run_next_action
