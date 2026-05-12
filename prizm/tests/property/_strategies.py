"""Hypothesis strategy generators for prizm property tests.

Implements the deferred property-test generators per design v6 §20.6 and §27.1#5.

Three top-level strategies:

* ``valid_state_strategy()``  — well-formed ``state.json`` dicts.
* ``valid_artifact_strategy(name)`` — minimal valid examples for each of
  the 9 artifact types (``01_problem`` … ``07_critique``).
* ``valid_user_decision_strategy()`` — strings the state-driver's
  ``_apply_user_decision`` accepts (drawn from
  ``scripts/next_action.py``).

Constraints applied to ``valid_state_strategy``:

- ``loop_depth <= max_loops``;
- ``current_stage`` is "later" than every entry in ``completed_stages``
  (i.e. ``completed_stages`` is a strict prefix of the canonical stage
  order ending strictly before ``current_stage``);
- ``retry_counts`` keys are valid stage values; values are 0..3.

Strategies stay deliberately small and deterministic so property tests
run in well under the §20.9 60s budget. ``max_examples=20`` at the call
site is sufficient.
"""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st


# --- Stage order (closed set per design v6 §20.5) ------------------------

# Mirrors scripts/_common.py::Stage. Hard-coded here to keep the strategy
# module zero-imports of plugin code (so it can run before sys.path is
# wired up by conftest in unusual harnesses).
STAGE_ORDER: list[str] = [
    "init",
    "framer",
    "check_framing_confidence",
    "select_matrix",
    "stage_e_check",
    "mapping_phase1",
    "compare_mappings",
    "mapping_phase2",
    "lookup",
    "interpret",
    "merge_interpretations",
    "synthesize",
    "critique",
    "check_fatal_severity",
    "assemble",
    "done",
]

# A fixed sample of valid matrix ids drawn from the live registry. Chosen
# to span numeric (altshuller, biotriz_bio) and prefixed (triz_ai_50x50)
# parameter id styles for coverage of the divergent code paths.
VALID_MATRIX_IDS: list[str] = [
    "altshuller_39x39",
    "biotriz_6x6_bio",
    "triz_ai_50x50",
]

# User-decision strings recognized by next_action.py::_apply_user_decision.
# The tail four (provide_more_detail, retry_subagent, skip_and_continue,
# abort_run) are reserved per the task spec but not yet wired into the
# state-driver; we still emit them so future driver work has property
# coverage in place. They round-trip through the JSON CLI but currently
# trigger ``unknown user decision choice`` — that surface is verified
# by tests/integration/test_user_decisions.py::test_unknown_decision_self_corrects.
USER_DECISION_CHOICES: list[str] = [
    "drop_fatal_proceed",
    "accept_with_override",
    "abandon_with_writeup",
    "proceed_anyway",  # reserved
    "abandon",  # reserved (alias for abort)
    "retry_subagent",  # reserved
    "skip_and_continue",  # reserved
    "abort_run",  # reserved (alias for abort)
    "provide_clarification",
    "override_matrix",
    "reformulate_with_constraint",
    "try_different_matrix",
    "accept_as_is",
    "edit_artifact",
    "abort",
]


# --- valid_state_strategy ------------------------------------------------

def _retry_counts_strategy() -> st.SearchStrategy[dict[str, int]]:
    """Per-stage retry counters. Keys are stage names; values are 0..3.

    Uses ``dictionaries`` with a small max_size to keep generated states
    legible during shrinking.
    """
    return st.dictionaries(
        keys=st.sampled_from(STAGE_ORDER),
        values=st.integers(min_value=0, max_value=3),
        max_size=4,
    )


def _flags_strategy() -> st.SearchStrategy[dict[str, Any]]:
    return st.fixed_dictionaries({
        "auto_loop": st.booleans(),
        "no_critique": st.booleans(),
        "no_resolution": st.booleans(),
    })


def _selected_matrices_strategy() -> st.SearchStrategy[list[str]]:
    return st.lists(
        st.sampled_from(VALID_MATRIX_IDS),
        min_size=0,
        max_size=3,
        unique=True,
    )


@st.composite
def valid_state_strategy(draw) -> dict[str, Any]:
    """Produce a coherent ``state.json`` dict.

    Coherence rules enforced:

    1. ``current_stage`` is drawn from STAGE_ORDER.
    2. ``completed_stages`` is a strict prefix of STAGE_ORDER ending
       *before* ``current_stage`` — so a state at "lookup" reports the
       stages init..interpret-prerequisites as done. This mirrors how
       ``_advance_stage`` actually constructs ``completed_stages``.
    3. ``loop_depth <= max_loops``.
    4. ``retry_counts`` values are 0..3 (the per-stage cap).
    """
    cur_idx = draw(st.integers(min_value=0, max_value=len(STAGE_ORDER) - 1))
    current_stage = STAGE_ORDER[cur_idx]

    # completed_stages = strict prefix [0..cur_idx) — may also be a
    # shorter prefix to cover replay scenarios where intermediate stages
    # haven't been re-marked complete yet.
    prefix_len = draw(st.integers(min_value=0, max_value=cur_idx))
    completed_stages = STAGE_ORDER[:prefix_len]

    max_loops = draw(st.integers(min_value=1, max_value=5))
    loop_depth = draw(st.integers(min_value=0, max_value=max_loops))

    selected_matrices = draw(_selected_matrices_strategy())
    retry_counts = draw(_retry_counts_strategy())
    flags = draw(_flags_strategy())

    run_id = draw(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
        min_size=4,
        max_size=24,
    ).filter(lambda s: s and not s.startswith("-")))

    state: dict[str, Any] = {
        "run_id": f"prop-{run_id}",
        "current_stage": current_stage,
        "completed_stages": list(completed_stages),
        "selected_matrices": selected_matrices,
        "retry_counts": retry_counts,
        "loop_depth": loop_depth,
        "max_loops": max_loops,
        "flags": flags,
        "user_prompt": "Property-test problem",
        "created_at": 1.0,
        "compatibility_checked": True,
    }
    return state


# --- valid_artifact_strategy --------------------------------------------

# Each artifact-builder returns a SearchStrategy producing a minimal
# example that satisfies the schema. The schemas in
# prizm/schemas/ mark many fields with ``minLength: 1`` /
# ``minItems: 1``; we honor those without trying to be exhaustive.

_LINEAGE_VALUES = [
    "altshuller-40",
    "biotriz-40",
    "drug-safety-reframed",
    "triz-ai-extended",
]

_CONFIDENCE_VALUES = ["high", "medium", "low"]
_SEVERITY_VALUES = ["minor", "moderate", "severe", "fatal"]


def _01_problem_strategy() -> st.SearchStrategy[dict]:
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "improving_concept": st.text(min_size=1, max_size=20),
        "worsening_concept": st.text(min_size=1, max_size=20),
        "domain_signals": st.lists(st.text(min_size=1, max_size=10),
                                   min_size=0, max_size=3),
        "exotic_signals": st.lists(st.text(min_size=1, max_size=10),
                                   min_size=0, max_size=2),
        "contradiction_type": st.sampled_from([
            "engineering-contradiction", "physical-contradiction",
        ]),
        "domain_class": st.text(min_size=1, max_size=15),
        "framing_confidence": st.sampled_from(_CONFIDENCE_VALUES),
        "constraints": st.lists(st.text(min_size=1, max_size=20),
                                min_size=0, max_size=3),
    })


def _02_selection_strategy() -> st.SearchStrategy[dict]:
    selected_entry = st.fixed_dictionaries({
        "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
        "score": st.floats(min_value=0.0, max_value=100.0,
                           allow_nan=False, allow_infinity=False),
        "rationale": st.text(min_size=1, max_size=20),
        "selection_confidence": st.sampled_from(_CONFIDENCE_VALUES),
    })
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "weights_version": st.sampled_from(["v0", "v1-software"]),
        "selected_matrices": st.lists(selected_entry, min_size=1, max_size=2),
        "rejected_matrices": st.just([]),
        "run_strategy": st.sampled_from(["single", "parallel"]),
        "stage_e_invoked": st.booleans(),
    })


def _03_mapping_strategy() -> st.SearchStrategy[dict]:
    alt_entry = st.fixed_dictionaries({
        "improving_param_id": st.text(min_size=1, max_size=4),
        "worsening_param_id": st.text(min_size=1, max_size=4),
        "alt_strength": st.sampled_from(_CONFIDENCE_VALUES),
    })
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
        "improving_param_id": st.text(min_size=1, max_size=4),
        "worsening_param_id": st.text(min_size=1, max_size=4),
        "improving_rationale": st.text(min_size=1, max_size=20),
        "worsening_rationale": st.text(min_size=1, max_size=20),
        "alternatives": st.lists(alt_entry, min_size=0, max_size=2),
        "mapping_confidence": st.sampled_from(_CONFIDENCE_VALUES),
        "no_clean_mapping": st.booleans(),
    })


def _03b_mapping_critique_strategy() -> st.SearchStrategy[dict]:
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
        "verdict": st.sampled_from(["agree", "disagree", "propose_third"]),
        "chosen_mapping": st.fixed_dictionaries({
            "improving_param_id": st.text(min_size=1, max_size=4),
            "worsening_param_id": st.text(min_size=1, max_size=4),
        }),
        "rationale": st.text(min_size=1, max_size=20),
    })


def _03c_independent_mapping_strategy() -> st.SearchStrategy[dict]:
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
        "improving_param_id": st.text(min_size=1, max_size=4),
        "worsening_param_id": st.text(min_size=1, max_size=4),
        "rationale": st.text(min_size=1, max_size=20),
        "confidence": st.sampled_from(_CONFIDENCE_VALUES),
        "no_clean_mapping": st.booleans(),
    })


def _04_principles_strategy() -> st.SearchStrategy[dict]:
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
        "populated": st.booleans(),
        "principles": st.lists(st.integers(min_value=1, max_value=40),
                               min_size=0, max_size=4, unique=True),
        "alternatives_tried": st.just([]),
    })


_CANONICAL_ID = st.sampled_from(["P_SEGMENTATION", "P_LOCAL_QUALITY",
                                 "P_DYNAMICS", "P_PRELIMINARY_ACTION"])


def _interpretation_entry_strategy() -> st.SearchStrategy[dict]:
    return st.fixed_dictionaries({
        "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
        "principle_id": st.sampled_from(["1", "2", "10", "15"]),
        "principle_canonical_id": _CANONICAL_ID,
        "principle_name": st.text(min_size=1, max_size=20),
        "interpretation_lineage": st.sampled_from(_LINEAGE_VALUES),
        "concrete_suggestion": st.text(min_size=1, max_size=30),
        "applies_how": st.text(min_size=1, max_size=30),
    })


def _05_interpretation_single_strategy() -> st.SearchStrategy[dict]:
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
        "principle_id": st.sampled_from(["1", "2", "10", "15"]),
        "principle_canonical_id": _CANONICAL_ID,
        "principle_name": st.text(min_size=1, max_size=20),
        "interpretation_lineage": st.sampled_from(_LINEAGE_VALUES),
        "concrete_suggestion": st.text(min_size=1, max_size=30),
        "applies_how": st.text(min_size=1, max_size=30),
    })


def _05_interpretations_strategy() -> st.SearchStrategy[dict]:
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "interpretations": st.lists(_interpretation_entry_strategy(),
                                    min_size=0, max_size=3),
    })


def _06_solutions_strategy() -> st.SearchStrategy[dict]:
    candidate = st.fixed_dictionaries({
        "name": st.text(min_size=1, max_size=20),
        "summary": st.text(min_size=1, max_size=30),
        "principles_applied": st.lists(_CANONICAL_ID, min_size=1,
                                       max_size=2, unique=True),
        "interpretation_refs": st.lists(
            st.fixed_dictionaries({
                "matrix_id": st.sampled_from(VALID_MATRIX_IDS),
                "principle_id": st.sampled_from(["1", "2", "10"]),
            }),
            min_size=1, max_size=2,
        ),
        "implementation_sketch": st.text(min_size=1, max_size=30),
        "novelty_estimate": st.sampled_from(_CONFIDENCE_VALUES),
        "effort_estimate": st.sampled_from(_CONFIDENCE_VALUES),
    })
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "candidates": st.lists(candidate, min_size=1, max_size=3),
    })


def _07_critique_strategy() -> st.SearchStrategy[dict]:
    sec = st.fixed_dictionaries({
        "improving": st.text(min_size=1, max_size=20),
        "worsening": st.text(min_size=1, max_size=20),
        "severity": st.sampled_from(_SEVERITY_VALUES),
    })
    crit = st.fixed_dictionaries({
        "candidate_name": st.text(min_size=1, max_size=20),
        "secondary_contradictions": st.lists(sec, min_size=0, max_size=2),
        "severity": st.sampled_from(_SEVERITY_VALUES),
        "risks": st.lists(st.text(min_size=1, max_size=20),
                          min_size=0, max_size=2),
        "recommendation": st.text(min_size=1, max_size=30),
    })
    return st.fixed_dictionaries({
        "schema_version": st.just(1),
        "per_solution_critiques": st.lists(crit, min_size=1, max_size=3),
    })


_ARTIFACT_BUILDERS: dict[str, "callable"] = {
    "01_problem": _01_problem_strategy,
    "02_selection": _02_selection_strategy,
    "03_mapping": _03_mapping_strategy,
    "03b_mapping_critique": _03b_mapping_critique_strategy,
    "03c_independent_mapping": _03c_independent_mapping_strategy,
    "04_principles": _04_principles_strategy,
    "05_interpretation_single": _05_interpretation_single_strategy,
    "05_interpretations": _05_interpretations_strategy,
    "06_solutions": _06_solutions_strategy,
    "07_critique": _07_critique_strategy,
}


def valid_artifact_strategy(name: str) -> st.SearchStrategy[dict]:
    """Return a strategy producing a minimal valid example for ``name``.

    ``name`` is the artifact-type prefix used by
    ``scripts/_common.py::schema_for_artifact``: ``01_problem``,
    ``02_selection``, ``03_mapping``, ``03b_mapping_critique``,
    ``03c_independent_mapping``, ``04_principles``,
    ``05_interpretation_single``, ``05_interpretations``,
    ``06_solutions``, ``07_critique``.
    """
    if name not in _ARTIFACT_BUILDERS:
        raise KeyError(
            f"unknown artifact name {name!r}; "
            f"valid keys: {sorted(_ARTIFACT_BUILDERS)}"
        )
    return _ARTIFACT_BUILDERS[name]()


# --- valid_user_decision_strategy ---------------------------------------

@st.composite
def valid_user_decision_strategy(draw) -> str:
    """Produce a user-decision string the state-driver currently
    recognizes — or one of the reserved aliases (per task spec).

    Some decisions take an inline payload value (constraint text, matrix
    id). For those, we append a ``:<value>`` suffix in the same shape the
    task spec uses so the strategy round-trips for the
    ``provide_more_detail:<text>`` family of inputs.
    """
    choice = draw(st.sampled_from(USER_DECISION_CHOICES))
    if choice in {"reformulate_with_constraint"}:
        text = draw(st.text(alphabet="abcdef ", min_size=3, max_size=10))
        return f"{choice}:{text.strip() or 'x'}"
    if choice in {"try_different_matrix", "override_matrix"}:
        return f"{choice}:{draw(st.sampled_from(VALID_MATRIX_IDS))}"
    return choice
