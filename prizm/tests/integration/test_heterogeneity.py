"""Layer-7 heterogeneity tests (design v6 §20.12).

These exist independently of the fixture-based state tests so that corpus
changes can't quietly disable them. Each test exercises one known edge case
of the heterogeneous matrix corpus.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure the scripts/ dir is importable.
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
for p in (str(PLUGIN_ROOT), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import _common  # noqa: E402
from scripts.select_matrix import select  # noqa: E402
from scripts.lookup_principles import lookup  # noqa: E402


@pytest.fixture(scope="module")
def registry(live_matrices_path):
    return json.loads(
        (live_matrices_path / "registry.json").read_text(encoding="utf-8")
    )


# --- T1 — mann shell matrix dropped at Stage A ---------------------------

def test_mann_shell_dropped_at_stage_a(live_matrices_path):
    """mann_matrix2003_48x48 is status=shell with populated_cells=0.

    Stage A must drop it; it MUST NOT appear in selected_matrices for any
    problem matching mann's mechanical/manufacturing domain.
    """
    mann_file = live_matrices_path / "matrices" / "mann_matrix2003_48x48.json"
    if not mann_file.exists():
        pytest.skip(
            "mann_matrix2003_48x48.json not present on disk (license-restricted; "
            "see MATRICES_OPTIONAL.md). Test is intentionally skipped in distributions "
            "that do not bundle this matrix."
        )
    # Force the matrices_root for select_matrix's internal _common loader.
    os.environ["TRIZ_MATRICES_PATH"] = str(live_matrices_path)
    _common._LOAD_CACHE.clear()
    problem = {
        "schema_version": 1,
        "improving_concept": "weight",
        "worsening_concept": "strength",
        "domain_signals": ["mechanical", "manufacturing"],
        "exotic_signals": [],
        "contradiction_type": "engineering-contradiction",
        "domain_class": "mechanical",
        "framing_confidence": "high",
        "constraints": [],
    }
    sel = select(problem)
    selected_ids = [m["matrix_id"] for m in sel.get("selected_matrices", [])]
    rejected_ids = [r["matrix_id"] for r in sel.get("rejected_matrices", [])]
    assert "mann_matrix2003_48x48" not in selected_ids, (
        f"mann shell matrix wrongly selected: {selected_ids}"
    )
    assert "mann_matrix2003_48x48" in rejected_ids, (
        f"mann shell matrix not rejected: {rejected_ids}"
    )


# --- T2 — biotriz bio and tech are distinct ids --------------------------

def test_biotriz_bio_and_tech_distinct_ids(registry, live_matrices_path):
    """biotriz_6x6_bio and biotriz_6x6_tech must both exist in the registry
    as distinct ids; lookup_principles against each returns its own cells."""
    ids = {m["id"] for m in registry.get("matrices", [])}
    assert "biotriz_6x6_bio" in ids, "biotriz_6x6_bio not in registry"
    # biotriz_6x6_tech may not have shipped yet; this catches that gap.
    if "biotriz_6x6_tech" not in ids:
        pytest.skip(
            "biotriz_6x6_tech not in registry; v6 §20.12 expects both. "
            "Phase-0 deliverable #6 must split BioTRIZ before this test enforces."
        )
    # Lookup against each returns its own cells.
    os.environ["TRIZ_MATRICES_PATH"] = str(live_matrices_path)
    _common._LOAD_CACHE.clear()
    for mid in ("biotriz_6x6_bio", "biotriz_6x6_tech"):
        matrix = _common.load_matrix(mid)
        meta_id = (matrix.get("meta") or {}).get("id")
        assert meta_id == mid, f"meta.id={meta_id!r} for {mid!r}"
        # Sanity: at least one cell yields principles.
        cells = matrix.get("matrix") or {}
        any_populated = False
        for row in cells.values():
            if isinstance(row, dict):
                for v in row.values():
                    if isinstance(v, list) and v:
                        any_populated = True
                        break
                if any_populated:
                    break
        assert any_populated, f"{mid} has no populated cells"


# --- T3 — healthcare prefixed ids round-trip -----------------------------

def test_healthcare_prefixed_ids_round_trip(live_matrices_path):
    """healthcare_servqual uses prefixed ids (S1..S10 rows, T*..T19 cols).

    lookup_principles must accept them verbatim — no int coercion.
    """
    os.environ["TRIZ_MATRICES_PATH"] = str(live_matrices_path)
    _common._LOAD_CACHE.clear()
    matrix = _common.load_matrix("healthcare_servqual")
    style = (matrix.get("meta") or {}).get("parameter_id_style")
    assert style == "prefixed", f"expected prefixed parameter_id_style, got {style!r}"

    # Find a known populated (S, T) cell in the matrix.
    cells = matrix.get("matrix") or {}
    chosen = None
    for r, row in cells.items():
        if not r.startswith("S") or not isinstance(row, dict):
            continue
        for c, v in row.items():
            if isinstance(v, list) and v:
                chosen = (r, c, v)
                break
        if chosen:
            break
    assert chosen, "no populated S*/T* cell in healthcare_servqual"
    r, c, expected_principles = chosen

    mapping = {
        "schema_version": 1,
        "matrix_id": "healthcare_servqual",
        "improving_param_id": r,    # "S1"
        "worsening_param_id": c,    # e.g. "T19"
        "alternatives": [],
        "mapping_confidence": "high",
        "no_clean_mapping": False,
    }
    result = lookup("healthcare_servqual", mapping)
    assert result["populated"] is True
    assert result["principles"] == expected_principles, (
        f"lookup didn't round-trip prefixed ids: got {result['principles']!r}, "
        f"expected {expected_principles!r}"
    )


# --- T4 — drug_safety lineage routed to governance prompt ----------------

def test_drug_safety_lineage_routed_to_governance_prompt(live_matrices_path):
    """drug_safety_18x18 principles must declare interpretation_lineage =
    drug-safety-reframed so the interpreter applies the governance prompt
    variant (design v6 §9.5a)."""
    drug_file = live_matrices_path / "matrices" / "drug_safety_18x18.json"
    if not drug_file.exists():
        pytest.skip(
            "drug_safety_18x18.json not present on disk (CC BY-NC-ND 4.0; not bundled; "
            "see MATRICES_OPTIONAL.md). Test is intentionally skipped in distributions "
            "that do not include this matrix."
        )
    os.environ["TRIZ_MATRICES_PATH"] = str(live_matrices_path)
    _common._LOAD_CACHE.clear()
    matrix = _common.load_matrix("drug_safety_18x18")
    meta_lineage = (matrix.get("meta") or {}).get("interpretation_lineage")
    assert meta_lineage == "drug-safety-reframed", (
        f"drug_safety meta.interpretation_lineage={meta_lineage!r}"
    )
    principles = matrix.get("principles") or {}
    assert principles, "drug_safety has empty principles table"
    bad = []
    for pid, pdata in principles.items():
        lineage = (pdata or {}).get("interpretation_lineage")
        if lineage != "drug-safety-reframed":
            bad.append((pid, lineage))
    assert not bad, (
        f"drug_safety principles with wrong interpretation_lineage: "
        f"{bad[:5]}{' ...' if len(bad) > 5 else ''}"
    )


# --- T5 — innovatetriz bilingual filter --------------------------------

def test_innovatetriz_bilingual_filtered_when_lang_not_supported(
    registry, live_matrices_path,
):
    """innovatetriz_extended is zh+en. v0.1's English-only Stage A filter
    must NOT drop it (en intersects supported), even though it also carries
    zh — that's the whole point of treating language as a SET.
    """
    os.environ["TRIZ_MATRICES_PATH"] = str(live_matrices_path)
    _common._LOAD_CACHE.clear()

    entry = next(
        (m for m in registry["matrices"] if m["id"] == "innovatetriz_extended"),
        None,
    )
    assert entry, "innovatetriz_extended missing from registry"
    assert "en" in entry["language"], (
        f"innovatetriz_extended language={entry['language']!r}; "
        f"test premise (en included) is wrong"
    )

    # Run Stage A via select(); the rejected_matrices list must NOT contain
    # innovatetriz with a language reason. (It MAY be rejected by Stage B's
    # experimental gate at high confidence — but not by Stage A language.)
    problem = {
        "schema_version": 1,
        "improving_concept": "speed",
        "worsening_concept": "complexity",
        "domain_signals": ["software"],
        "exotic_signals": [],
        "contradiction_type": "engineering-contradiction",
        "domain_class": "software",
        "framing_confidence": "medium",  # avoid Stage B experimental drop
        "constraints": [],
    }
    sel = select(problem)
    rejected_for_lang = [
        r for r in sel.get("rejected_matrices", [])
        if r["matrix_id"] == "innovatetriz_extended"
        and "language" in r.get("reason", "")
    ]
    assert not rejected_for_lang, (
        f"innovatetriz wrongly rejected for language: {rejected_for_lang}"
    )
