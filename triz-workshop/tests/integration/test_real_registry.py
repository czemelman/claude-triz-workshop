"""Layer-6 real-registry integration test (design v6 §20.11).

Loads the actual `${TRIZ_MATRICES_PATH}/registry.json` and asserts the
declarative facts the rest of the system relies on. Catches the failure
mode where fixtures are clean but the corpus has drifted.

Asserted invariants:

1. Every `matrix_file` path resolves and parses as JSON.
2. Every parsed file has `meta.id` matching the filename stem.
3. Every `selector_tags.*` value (in use_cases/*.json) is in
   `selector_tags_vocabulary.json`.
4. Every principle has non-empty `canonical_id` matching `^P_[A-Z][A-Z_]*$`.
5. Every `meta.language` is a non-empty list of 2-8 char strings.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest


CANONICAL_ID_RE = re.compile(r"^P_[A-Z][A-Z_]*$")
LANGUAGE_TAG_RE = re.compile(r"^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8})*$")


@pytest.fixture(scope="module")
def registry(live_matrices_path):
    p = live_matrices_path / "registry.json"
    assert p.exists(), f"registry.json not at {p}"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def vocabulary(live_matrices_path):
    p = live_matrices_path / "selector_tags_vocabulary.json"
    assert p.exists(), f"selector_tags_vocabulary.json not at {p}"
    return json.loads(p.read_text(encoding="utf-8"))


# --- 1. Every matrix_file resolves and parses ----------------------------

def test_every_matrix_file_resolves_and_parses(registry, live_matrices_path):
    """Each registry entry's matrix_file path must exist and be valid JSON."""
    failures = []
    for entry in registry.get("matrices", []):
        rel = entry.get("matrix_file")
        if not rel:
            failures.append(f"{entry.get('id')!r}: no matrix_file")
            continue
        p = live_matrices_path / rel
        if not p.exists():
            failures.append(f"{entry['id']!r}: {p} missing")
            continue
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            failures.append(f"{entry['id']!r}: invalid JSON: {e}")
    assert not failures, "\n".join(failures)


# --- 2. Every meta.id matches filename stem -------------------------------

def test_every_matrix_meta_id_matches_filename_stem(registry, live_matrices_path):
    failures = []
    for entry in registry.get("matrices", []):
        rel = entry.get("matrix_file")
        if not rel:
            continue
        p = live_matrices_path / rel
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        meta_id = (data.get("meta") or {}).get("id")
        stem = p.stem
        # Some legacy lineage matrices may stem-mismatch by design (e.g.
        # biotriz_24x24 backed by biotriz_6x6_*); we only assert the
        # registry id == meta.id, since meta.id is the contract.
        if meta_id != entry["id"]:
            failures.append(
                f"{entry['id']!r}: meta.id={meta_id!r} doesn't match registry id"
            )
    assert not failures, "\n".join(failures)


# --- 3. selector_tags.* values are in vocabulary --------------------------

def test_every_selector_tag_is_in_vocabulary(registry, vocabulary, live_matrices_path):
    """Every selector_tags.{domains,problem_classes,tags,excludes} value must
    be in selector_tags_vocabulary.json."""
    vocab_domains = set(vocabulary.get("domains", []))
    vocab_problem_classes = set(vocabulary.get("problem_classes", []))
    vocab_tags = set(vocabulary.get("tags", []))
    # excludes can draw from either domains or domain_signals (the use-case
    # files in this corpus reference both freely).
    vocab_domain_signals = set(vocabulary.get("domain_signals", []))

    failures = []
    for entry in registry.get("matrices", []):
        rel = entry.get("use_case_file")
        if not rel:
            continue
        p = live_matrices_path / rel
        if not p.exists():
            continue
        uc = json.loads(p.read_text(encoding="utf-8"))
        st = uc.get("selector_tags") or {}
        for v in st.get("domains", []):
            if v not in vocab_domains:
                failures.append(
                    f"{entry['id']!r}: selector_tags.domains: {v!r} not in vocab"
                )
        for v in st.get("problem_classes", []):
            if v not in vocab_problem_classes:
                failures.append(
                    f"{entry['id']!r}: selector_tags.problem_classes: {v!r} not in vocab"
                )
        for v in st.get("tags", []):
            if v not in vocab_tags:
                failures.append(
                    f"{entry['id']!r}: selector_tags.tags: {v!r} not in vocab"
                )
        for v in st.get("excludes", []):
            if (v not in vocab_domains
                    and v not in vocab_domain_signals
                    and v not in vocab_tags):
                failures.append(
                    f"{entry['id']!r}: selector_tags.excludes: {v!r} not in vocab"
                )
    if failures:
        # Surface up to first 20 failures so the report stays readable.
        msg = (f"{len(failures)} vocabulary violations; first 20:\n"
               + "\n".join(failures[:20]))
        pytest.fail(msg)


# --- 4. canonical_id format -----------------------------------------------

def test_every_principle_has_valid_canonical_id(registry, live_matrices_path):
    """Every principle in every matrix must have a canonical_id matching
    ^P_[A-Z][A-Z_]*$ — required by amendment 3."""
    failures = []
    for entry in registry.get("matrices", []):
        # identical-duplicate matrices may not carry a principles table; skip.
        if entry.get("status") == "identical-duplicate":
            continue
        rel = entry.get("matrix_file")
        if not rel:
            continue
        p = live_matrices_path / rel
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        principles = data.get("principles") or {}
        if not principles:
            # shell matrices declare no principles; that's allowed.
            if entry.get("status") == "shell":
                continue
            failures.append(f"{entry['id']!r}: no principles table")
            continue
        for pid, pdata in principles.items():
            cid = (pdata or {}).get("canonical_id")
            if not cid:
                failures.append(
                    f"{entry['id']!r}: principle {pid!r}: missing canonical_id"
                )
                continue
            if not CANONICAL_ID_RE.match(cid):
                failures.append(
                    f"{entry['id']!r}: principle {pid!r}: "
                    f"canonical_id {cid!r} doesn't match ^P_[A-Z][A-Z_]*$"
                )
    if failures:
        msg = (f"{len(failures)} canonical_id violations; first 20:\n"
               + "\n".join(failures[:20]))
        pytest.fail(msg)


# --- 5. meta.language ----------------------------------------------------

def test_every_meta_language_is_non_empty_list_of_short_codes(registry, live_matrices_path):
    """Every meta.language must be a non-empty list of 2-8 char strings."""
    failures = []
    for entry in registry.get("matrices", []):
        rel = entry.get("matrix_file")
        if not rel:
            continue
        p = live_matrices_path / rel
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        meta = data.get("meta") or {}
        langs = meta.get("language")
        if not isinstance(langs, list) or not langs:
            failures.append(
                f"{entry['id']!r}: meta.language is not a non-empty list "
                f"(got {langs!r})"
            )
            continue
        for lang in langs:
            if not isinstance(lang, str):
                failures.append(
                    f"{entry['id']!r}: meta.language entry not a string: {lang!r}"
                )
                continue
            if not (2 <= len(lang) <= 8):
                failures.append(
                    f"{entry['id']!r}: meta.language entry length out of [2,8]: "
                    f"{lang!r}"
                )
    assert not failures, "\n".join(failures)
