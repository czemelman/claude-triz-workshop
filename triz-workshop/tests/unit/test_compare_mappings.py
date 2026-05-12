"""Unit tests for next_action._compare_mappings (design v6 §15.2).

The decision tree:

1. mapper.no_clean_mapping OR critic.no_clean_mapping → NO_CLEAN_MAPPING
2. mapper.mapping_confidence == 'low' OR critic.confidence == 'low' → NO_CLEAN_MAPPING
3. both axes string-equal → AGREE
4. otherwise → DISAGREE
"""

from __future__ import annotations

from scripts.next_action import _compare_mappings
# Import Decision from the same module identity that next_action.py loads
# (scripts/_common.py via `import _common` after sys.path insertion). The
# scripts/__init__.py-less layout means `from scripts._common import Decision`
# would create a second, incompatible enum object — values match but the
# enum instances do not compare equal.
import _common  # noqa: E402

Decision = _common.Decision


def _mapper(imp="9", wor="14", conf="high", no_clean=False):
    return {
        "improving_param_id": imp,
        "worsening_param_id": wor,
        "mapping_confidence": conf,
        "no_clean_mapping": no_clean,
    }


def _critic(imp="9", wor="14", conf="high", no_clean=False):
    return {
        "improving_param_id": imp,
        "worsening_param_id": wor,
        "confidence": conf,
        "no_clean_mapping": no_clean,
    }


# --- AGREE branch ---------------------------------------------------------

def test_agree_when_both_axes_match_numeric():
    assert _compare_mappings(_mapper("9", "14"), _critic("9", "14")) == Decision.AGREE


def test_agree_when_both_axes_match_prefixed():
    assert _compare_mappings(
        _mapper("S1", "T19"), _critic("S1", "T19"),
    ) == Decision.AGREE


def test_agree_when_axes_match_with_medium_confidence():
    assert _compare_mappings(
        _mapper(conf="medium"), _critic(conf="medium"),
    ) == Decision.AGREE


# --- DISAGREE branch ------------------------------------------------------

def test_disagree_when_improving_axis_differs():
    assert _compare_mappings(_mapper("9", "14"), _critic("10", "14")) == Decision.DISAGREE


def test_disagree_when_worsening_axis_differs():
    assert _compare_mappings(_mapper("9", "14"), _critic("9", "15")) == Decision.DISAGREE


def test_disagree_when_both_axes_differ():
    assert _compare_mappings(_mapper("9", "14"), _critic("11", "16")) == Decision.DISAGREE


# --- NO_CLEAN_MAPPING branch ---------------------------------------------

def test_no_clean_when_mapper_flags_no_clean():
    assert _compare_mappings(
        _mapper(no_clean=True), _critic(),
    ) == Decision.NO_CLEAN_MAPPING


def test_no_clean_when_critic_flags_no_clean():
    assert _compare_mappings(
        _mapper(), _critic(no_clean=True),
    ) == Decision.NO_CLEAN_MAPPING


def test_no_clean_when_both_flag_no_clean():
    assert _compare_mappings(
        _mapper(no_clean=True), _critic(no_clean=True),
    ) == Decision.NO_CLEAN_MAPPING


def test_no_clean_when_mapper_low_confidence():
    assert _compare_mappings(
        _mapper(conf="low"), _critic(),
    ) == Decision.NO_CLEAN_MAPPING


def test_no_clean_when_critic_low_confidence():
    assert _compare_mappings(
        _mapper(), _critic(conf="low"),
    ) == Decision.NO_CLEAN_MAPPING


def test_no_clean_takes_precedence_over_disagree():
    # If axes differ AND someone flagged no_clean, NO_CLEAN_MAPPING wins
    # because the no-clean check is earlier in the decision tree.
    assert _compare_mappings(
        _mapper("9", "14", no_clean=True),
        _critic("11", "16"),
    ) == Decision.NO_CLEAN_MAPPING


# --- String-coercion edge cases ------------------------------------------

def test_numeric_string_vs_int_compare_as_strings():
    # Schema requires strings, but defensive: explicit str-coercion in
    # _compare_mappings means a stray int still compares correctly.
    m = {"improving_param_id": 9, "worsening_param_id": 14,
         "mapping_confidence": "high", "no_clean_mapping": False}
    c = {"improving_param_id": "9", "worsening_param_id": "14",
         "confidence": "high", "no_clean_mapping": False}
    assert _compare_mappings(m, c) == Decision.AGREE
