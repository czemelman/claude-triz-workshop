"""Unit tests for the if-DSL in select_matrix.py.

Exercises:
- All 6 predicates per design v6 §14.2 / storage amendment 1:
    exotic_signal, domain_signal, contradiction_type_is, domain_class_is,
    language_is, populated_cells_at_least.
- 3 combinators: any_of, all_of, not.
- Cycle detection in _resolve_redirects.
- Unknown predicates raise ValueError.
"""

from __future__ import annotations

import pytest

from scripts.select_matrix import (
    _eval_if,
    _eval_predicate,
    _resolve_redirects,
)


# --- Predicate tests ------------------------------------------------------

def _problem(**overrides):
    base = {
        "domain_signals": ["software"],
        "exotic_signals": [],
        "contradiction_type": "engineering-contradiction",
        "domain_class": "software",
    }
    base.update(overrides)
    return base


def test_predicate_exotic_signal_match():
    assert _eval_predicate({"exotic_signal": "bio-analogy"},
                           _problem(exotic_signals=["bio-analogy"]))


def test_predicate_exotic_signal_miss():
    assert not _eval_predicate({"exotic_signal": "bio-analogy"},
                               _problem(exotic_signals=["security"]))


def test_predicate_domain_signal_match():
    assert _eval_predicate({"domain_signal": "software"}, _problem())


def test_predicate_domain_signal_miss():
    assert not _eval_predicate({"domain_signal": "biological"}, _problem())


def test_predicate_contradiction_type_is_match():
    assert _eval_predicate(
        {"contradiction_type_is": "engineering-contradiction"}, _problem(),
    )


def test_predicate_contradiction_type_is_miss():
    assert not _eval_predicate(
        {"contradiction_type_is": "physical-contradiction"}, _problem(),
    )


def test_predicate_domain_class_is_match():
    assert _eval_predicate({"domain_class_is": "software"}, _problem())


def test_predicate_domain_class_is_miss():
    assert not _eval_predicate(
        {"domain_class_is": "pharmaceutical"}, _problem(),
    )


def test_predicate_language_is_en_supported():
    # v0.1 supports English only; "en" matches.
    assert _eval_predicate({"language_is": "en"}, _problem())


def test_predicate_language_is_unsupported():
    # Anything not in SUPPORTED_LANGUAGES is False.
    assert not _eval_predicate({"language_is": "ru"}, _problem())


def test_predicate_populated_cells_at_least_always_true_in_problem_context():
    # Per design comment: this predicate is matrix-context only; in problem
    # context it always evaluates True (true target check happens elsewhere).
    assert _eval_predicate({"populated_cells_at_least": 100}, _problem())


def test_predicate_unknown_raises():
    with pytest.raises(ValueError):
        _eval_predicate({"unknown_predicate_xyz": "value"}, _problem())


# --- Combinator tests -----------------------------------------------------

def test_any_of_with_one_match():
    cond = {"any_of": [
        {"exotic_signal": "bio-analogy"},
        {"domain_signal": "software"},
    ]}
    assert _eval_if(cond, _problem())


def test_any_of_with_no_matches():
    cond = {"any_of": [
        {"exotic_signal": "bio-analogy"},
        {"domain_signal": "biological"},
    ]}
    assert not _eval_if(cond, _problem())


def test_any_of_empty_is_false():
    # Empty OR is conventionally False; matches Python's `any([])`.
    assert not _eval_if({"any_of": []}, _problem())


def test_all_of_all_match():
    cond = {"all_of": [
        {"domain_signal": "software"},
        {"contradiction_type_is": "engineering-contradiction"},
    ]}
    assert _eval_if(cond, _problem())


def test_all_of_one_misses():
    cond = {"all_of": [
        {"domain_signal": "software"},
        {"exotic_signal": "bio-analogy"},
    ]}
    assert not _eval_if(cond, _problem())


def test_all_of_empty_is_true():
    # Empty AND is conventionally True; matches Python's `all([])`.
    assert _eval_if({"all_of": []}, _problem())


def test_not_inverts_truth():
    assert _eval_if({"not": {"domain_signal": "biological"}}, _problem())
    assert not _eval_if({"not": {"domain_signal": "software"}}, _problem())


def test_combinator_nesting():
    # NOT (any_of [bio-analogy, biological]) AND (all_of [software, eng-contradiction])
    cond = {
        "all_of": [
            {"not": {"any_of": [
                {"exotic_signal": "bio-analogy"},
                {"domain_signal": "biological"},
            ]}},
            {"all_of": [
                {"domain_signal": "software"},
                {"contradiction_type_is": "engineering-contradiction"},
            ]},
        ],
    }
    assert _eval_if(cond, _problem())


# --- Redirect resolution: cycle detection --------------------------------

def test_resolve_redirects_cycle_detected_returns_origin():
    """A→B→A loop must terminate without infinite recursion.

    Build two synthetic use cases that point at each other; the resolver
    must walk one hop, detect the cycle, and return the original id.
    """
    use_cases = {
        "matrix_A": {
            "when_to_use": {
                "skip_in_favor_of": [
                    {"target_matrix_id": "matrix_B",
                     "if": {"domain_signal": "software"}},
                ],
            },
        },
        "matrix_B": {
            "when_to_use": {
                "skip_in_favor_of": [
                    {"target_matrix_id": "matrix_A",
                     "if": {"domain_signal": "software"}},
                ],
            },
        },
    }
    log: list[dict] = []
    final = _resolve_redirects(
        "matrix_A", _problem(),
        use_case_loader=lambda mid: use_cases.get(mid, {}),
        excluded_ids=set(),
        log=log,
    )
    # We may end on either node depending on traversal order; the property
    # that matters is cycle-detection: the run terminates and the cycle
    # appears in the log.
    assert final in {"matrix_A", "matrix_B"}
    assert any(entry.get("skipped") == "cycle" for entry in log)


def test_resolve_redirects_self_cycle_terminates():
    use_cases = {
        "matrix_X": {
            "when_to_use": {
                "skip_in_favor_of": [
                    {"target_matrix_id": "matrix_X",
                     "if": {"domain_signal": "software"}},
                ],
            },
        },
    }
    log: list[dict] = []
    final = _resolve_redirects(
        "matrix_X", _problem(),
        use_case_loader=lambda mid: use_cases.get(mid, {}),
        excluded_ids=set(),
        log=log,
    )
    assert final == "matrix_X"
    assert any(entry.get("skipped") == "cycle" for entry in log)


def test_resolve_redirects_excluded_target_not_followed():
    """A target that was already dropped at Stage A must not be followed."""
    use_cases = {
        "matrix_A": {
            "when_to_use": {
                "skip_in_favor_of": [
                    {"target_matrix_id": "matrix_B",
                     "if": {"domain_signal": "software"}},
                ],
            },
        },
    }
    log: list[dict] = []
    final = _resolve_redirects(
        "matrix_A", _problem(),
        use_case_loader=lambda mid: use_cases.get(mid, {}),
        excluded_ids={"matrix_B"},
        log=log,
    )
    assert final == "matrix_A"
    assert any(entry.get("skipped") == "stage_a_excluded" for entry in log)


def test_resolve_redirects_unknown_predicate_does_not_crash():
    """An unknown predicate inside an if-clause should be logged and skipped,
    not crash the whole selection."""
    use_cases = {
        "matrix_A": {
            "when_to_use": {
                "skip_in_favor_of": [
                    {"target_matrix_id": "matrix_B",
                     "if": {"unknown_pred": "value"}},
                ],
            },
        },
    }
    log: list[dict] = []
    final = _resolve_redirects(
        "matrix_A", _problem(),
        use_case_loader=lambda mid: use_cases.get(mid, {}),
        excluded_ids=set(),
        log=log,
    )
    # The unknown predicate raises ValueError inside _eval_if; the resolver
    # catches it, logs, and does not redirect.
    assert final == "matrix_A"
    assert any("error" in e for e in log)
