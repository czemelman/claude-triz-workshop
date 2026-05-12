#!/usr/bin/env python3
"""next_action.py — THE STATE DRIVER (design v6 §6, §6.4, §19).

Pure-function-ish state-to-action mapper. Each invocation:

    1. Loads (or creates) the run's state.json
    2. Optionally applies a user decision from --user-input
    3. Validates the most recent artifact (if any)
    4. Emits ONE atomic JSON action for the orchestrator to execute

Strict CLI contract (design v6 §19.2):
    - Exit code is ALWAYS 0.
    - stdout is ALWAYS one valid JSON action object.
    - stderr is ALWAYS empty.

Action types (§6.3): dispatch_subagent, dispatch_subagents_parallel,
run_script, ask_user, self_correct, done.

Stages (§20.5 / §6.4): init → framer → check_framing_confidence →
select_matrix → stage_e_check → mapping_phase1 → compare_mappings →
[mapping_phase2] → lookup → interpret → merge_interpretations →
synthesize → critique → check_fatal_severity → assemble → done.
"""

from __future__ import annotations

# --- Subprocess coverage hook (must run before any heavy imports) ---------
# Activates coverage.process_startup() iff COVERAGE_PROCESS_START is in env.
# No-op otherwise. The import is wrapped so a missing _coverage_init never
# breaks the CLI contract — production runs without coverage installed are
# unaffected. Placing this above the rest of the imports means the trace
# function is patched in before _common, jsonschema, etc. load, so their
# top-level code is also measured.
import os as _os_pre  # noqa: E402
import sys as _sys_pre  # noqa: E402
from pathlib import Path as _Path_pre  # noqa: E402

_HERE_PRE = _Path_pre(__file__).resolve().parent
if str(_HERE_PRE) not in _sys_pre.path:
    _sys_pre.path.insert(0, str(_HERE_PRE))
try:
    from _coverage_init import *  # noqa: F401,F403,E402  -- coverage instrumentation; no-op without env
except ImportError:
    pass
del _os_pre, _sys_pre, _Path_pre, _HERE_PRE

import argparse
import io
import json
import os
import shlex
import sys
import time
import uuid
from contextlib import redirect_stderr
from pathlib import Path

import jsonschema

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402

# Per-stage retry cap (design v6 §19.3).
MAX_RETRIES_PER_STAGE = 3
DEFAULT_MAX_LOOPS = 2
INTERPRETER_BATCH_SIZE = 7


# --- Action emission ------------------------------------------------------

def _emit(action: dict) -> int:
    """Print a single JSON object to stdout. Always returns 0."""
    sys.stdout.write(json.dumps(action, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return 0


def _emit_self_correct(message: str, hint: str | None = None) -> int:
    payload = {
        "action": "self_correct",
        "message": message,
    }
    if hint:
        payload["hint"] = hint
    return _emit(payload)


def _emit_done(run_id: str | None = None, report_path: str | None = None) -> int:
    payload = {"action": "done"}
    if run_id:
        payload["run_id"] = run_id
    if report_path:
        payload["report_path"] = report_path
    return _emit(payload)


def _emit_ask_user(kind: str, run_id: str, **extra) -> int:
    payload = {"action": "ask_user", "kind": kind, "run_id": run_id}
    payload.update(extra)
    # State-driver also persists the awaiting-decision payload to disk so a
    # killed orchestrator can be resumed without losing the prompt context.
    try:
        rd = _common.run_dir(run_id)
        _common.atomic_write(rd / "awaiting_decision.json", payload)
    except Exception:
        pass
    return _emit(payload)


# --- Argparse hardening ---------------------------------------------------

def _parse_args_safely(argv: list[str]) -> tuple[argparse.Namespace | None, str | None]:
    """Per design v6 §19.1: argparse errors must NOT exit(2).

    argparse normally calls sys.exit(2) on invalid args; we capture stderr,
    suppress its exit, and return an error message the caller will surface
    via emit_self_correct.
    """
    parser = argparse.ArgumentParser(
        prog="next_action.py",
        description="Emit the single next action for a prizm run.",
        add_help=True,
    )
    parser.add_argument("--run-id", default=None,
                        help="Run id. Required unless --new-run.")
    parser.add_argument("--user-input", default=None,
                        help="JSON-encoded user response to a prior ask_user.")
    parser.add_argument("--new-run", action="store_true",
                        help="Initialize a new run. Generates a run-id if --run-id not supplied.")
    parser.add_argument("--user-prompt", default=None,
                        help="The user's free-text problem statement; required with --new-run.")
    parser.add_argument("--replay-from", default=None,
                        help="Replay an existing run starting from a specific stage.")

    # When --help / -h is in argv, let argparse print and exit normally (the
    # caller in __main__ swallows SystemExit and emits a self_correct only on
    # nonzero codes).
    err_buf = io.StringIO()
    try:
        with redirect_stderr(err_buf):
            args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse exits 0 on --help, 2 on errors. Treat 0 as "user asked
        # for help" — re-raise so the help text reaches stderr/stdout normally
        # in direct CLI use; in production the orchestrator never passes -h.
        if int(getattr(e, "code", 0) or 0) == 0:
            raise
        msg = err_buf.getvalue().strip() or "argparse failure"
        return None, msg
    return args, None


# --- State management -----------------------------------------------------

def _new_state(run_id: str, user_prompt: str | None) -> dict:
    return {
        "run_id": run_id,
        "current_stage": _common.Stage.INIT.value,
        "completed_stages": [],
        "selected_matrices": [],
        "retry_counts": {},
        "loop_depth": 0,
        "max_loops": DEFAULT_MAX_LOOPS,
        "flags": {},
        "user_prompt": user_prompt or "",
        "created_at": time.time(),
        "compatibility_checked": False,
    }


def _load_state(run_id: str) -> dict:
    p = _common.run_dir(run_id, create=False) / "state.json"
    if not p.exists():
        raise FileNotFoundError(f"state.json not found for run {run_id}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _persist_state(state: dict) -> None:
    rd = _common.run_dir(state["run_id"])
    _common.atomic_write(rd / "state.json", state)


def _bump_retry(state: dict, stage: str) -> int:
    rc = state.setdefault("retry_counts", {})
    rc[stage] = int(rc.get(stage, 0)) + 1
    return rc[stage]


def _get_retry(state: dict, stage: str) -> int:
    return int(state.get("retry_counts", {}).get(stage, 0))


def _advance_stage(state: dict, next_stage: _common.Stage) -> None:
    cur = state.get("current_stage")
    if cur and cur not in state.setdefault("completed_stages", []):
        state["completed_stages"].append(cur)
    state["current_stage"] = next_stage.value


# --- Argument parsing for the user_prompt --------------------------------

def _parse_user_prompt(user_prompt: str) -> tuple[str, dict]:
    """Extract --matrix=, --no-mapping-critic, --max-loops=N etc from prompt.

    Returns (problem_text, flags_dict).
    """
    flags = {
        "matrix_overrides": [],
        "matrices_overrides": [],
        "auto_loop": False,
        "max_loops": DEFAULT_MAX_LOOPS,
        "no_critique": False,
        "no_mapping_critic": False,
    }
    if not user_prompt:
        return "", flags
    try:
        tokens = shlex.split(user_prompt)
    except ValueError:
        # Unbalanced quotes etc; fall back to the raw text.
        return user_prompt, flags
    leftover: list[str] = []
    for tok in tokens:
        if tok.startswith("--matrix="):
            flags["matrix_overrides"].append(tok.split("=", 1)[1])
        elif tok.startswith("--matrices="):
            flags["matrices_overrides"].extend(
                m for m in tok.split("=", 1)[1].split(",") if m
            )
        elif tok == "--auto-loop":
            flags["auto_loop"] = True
        elif tok.startswith("--max-loops="):
            try:
                flags["max_loops"] = int(tok.split("=", 1)[1])
            except ValueError:
                pass
        elif tok == "--no-critique":
            flags["no_critique"] = True
        elif tok == "--no-mapping-critic":
            flags["no_mapping_critic"] = True
        else:
            leftover.append(tok)
    return " ".join(leftover).strip(), flags


# --- Decision: compare_mappings (design v6 §15.2) -------------------------

def _is_prefixed_matrix(matrix_id: str) -> bool:
    try:
        m = _common.load_matrix(matrix_id)
        return (m.get("meta") or {}).get("parameter_id_style") == "prefixed"
    except Exception:
        return False


def _compare_mappings(mapper: dict, critic_indep: dict) -> _common.Decision:
    """Mechanical comparison per design v6 §15.2.

    AGREE: both axes match (string-eq for prefixed matrices; otherwise still
    string-eq because schema requires strings).
    NO_CLEAN_MAPPING: mapper or critic flagged it, OR confidence is low.
    DISAGREE: anything else.
    """
    if mapper.get("no_clean_mapping") or critic_indep.get("no_clean_mapping"):
        return _common.Decision.NO_CLEAN_MAPPING
    if mapper.get("mapping_confidence") == "low" or critic_indep.get("confidence") == "low":
        return _common.Decision.NO_CLEAN_MAPPING
    # String equality on both axes (works for both numeric "9" and prefixed "S1").
    if (str(mapper.get("improving_param_id")) == str(critic_indep.get("improving_param_id"))
            and str(mapper.get("worsening_param_id")) == str(critic_indep.get("worsening_param_id"))):
        return _common.Decision.AGREE
    return _common.Decision.DISAGREE


# --- Stage handlers -------------------------------------------------------

def _action_run_framer(run_id: str, user_prompt: str) -> dict:
    return {
        "action": "dispatch_subagent",
        "subagent": "triz-problem-framer",
        "run_id": run_id,
        "expected_artifact": "01_problem.json",
        "prompt": (
            "User problem:\n\n"
            f"{user_prompt}\n\n"
            f"Frame this as a TRIZ contradiction. Write your output to "
            f"`.triz/runs/{run_id}/01_problem.json`. Conform to "
            f"01_problem.schema.json: improving_concept, worsening_concept, "
            f"domain_signals, exotic_signals (drawn from selector_tags_vocabulary.json), "
            f"contradiction_type, domain_class, framing_confidence (high/medium/low), "
            f"and constraints. Set framing_confidence=low if the problem is ambiguous."
        ),
    }


def _action_run_selector_subagent(run_id: str) -> dict:
    return {
        "action": "dispatch_subagent",
        "subagent": "triz-matrix-selector",
        "run_id": run_id,
        "expected_artifact": "02_selection.json",
        "prompt": (
            f"Stage D scoring produced a near-tie (top vs second margin <15%). "
            f"Inspect `.triz/runs/{run_id}/02_selection.json` and the candidate "
            f"matrices' use_case files. You may rewrite 02_selection.json with: "
            f"a different selected_matrices set; an updated run_strategy "
            f"('single' or 'parallel'); updated rationales. Preserve "
            f"weights_version, schema_version, and stage_e_invoked=true."
        ),
    }


def _action_mapper_and_critic_for(matrix_id: str, run_id: str, problem: dict, no_critic: bool) -> list[dict]:
    """Phase-1 dispatch per matrix: mapper + (independent) critic in parallel.

    The critic is structurally blinded — its prompt does NOT mention the
    mapper or the mapper's output. Phase 2 deliberation only happens later
    if compare_mappings says DISAGREE.
    """
    mapping_path = f".triz/runs/{run_id}/03_mapping_{matrix_id}.json"
    indep_path = f".triz/runs/{run_id}/03c_independent_mapping_{matrix_id}.json"
    problem_blob = json.dumps({
        "improving_concept": problem.get("improving_concept"),
        "worsening_concept": problem.get("worsening_concept"),
        "domain_signals": problem.get("domain_signals"),
        "exotic_signals": problem.get("exotic_signals"),
        "contradiction_type": problem.get("contradiction_type"),
        "domain_class": problem.get("domain_class"),
        "constraints": problem.get("constraints"),
    }, indent=2)
    dispatches = [
        {
            "subagent": "triz-parameter-mapper",
            "run_id": run_id,
            "expected_artifact": f"03_mapping_{matrix_id}.json",
            "prompt": (
                f"Map this contradiction onto matrix `{matrix_id}`. Read the "
                f"matrix file from registry to learn its parameter set and "
                f"meta.parameter_id_style. Honor that style verbatim. Output "
                f"to `{mapping_path}` per 03_mapping.schema.json. Provide 1-3 "
                f"alternative FULL pairs (improving, worsening) in `alternatives`. "
                f"Set no_clean_mapping=true if no parameter pair fits well.\n\n"
                f"Problem:\n{problem_blob}"
            ),
        },
    ]
    if not no_critic:
        dispatches.append({
            "subagent": "triz-mapping-critic",
            "run_id": run_id,
            "expected_artifact": f"03c_independent_mapping_{matrix_id}.json",
            "prompt": (
                f"Independently produce your own mapping of this contradiction "
                f"onto matrix `{matrix_id}` (Phase 1 — INDEPENDENT, blind to "
                f"any prior mapping). Output to `{indep_path}` per "
                f"03c_independent_mapping.schema.json.\n\n"
                f"Problem:\n{problem_blob}"
            ),
        })
    return dispatches


def _action_phase2_critic(matrix_id: str, run_id: str) -> dict:
    return {
        "action": "dispatch_subagent",
        "subagent": "triz-mapping-critic",
        "run_id": run_id,
        "expected_artifact": f"03b_mapping_critique_{matrix_id}.json",
        "prompt": (
            f"Phase 2 (deliberation). Your independent mapping at "
            f"`.triz/runs/{run_id}/03c_independent_mapping_{matrix_id}.json` "
            f"disagrees with the mapper's at "
            f"`.triz/runs/{run_id}/03_mapping_{matrix_id}.json`. Read both. "
            f"Decide: agree (concede to mapper), disagree (keep your independent "
            f"mapping), or propose_third (neither is right). Write the verdict "
            f"to `.triz/runs/{run_id}/03b_mapping_critique_{matrix_id}.json` "
            f"per 03b_mapping_critique.schema.json."
        ),
    }


def _action_lookup_for(matrix_id: str, run_id: str) -> dict:
    return {
        "action": "run_script",
        "script": "lookup_principles.py",
        "args": ["--run-id", run_id, "--matrix", matrix_id],
        "run_id": run_id,
        "expected_artifact": f"04_principles_{matrix_id}.json",
    }


def _action_interpret(run_id: str, batches: list[list[dict]]) -> dict:
    """Each batch is a list of (matrix_id, principle_id) jobs. We dispatch
    the entire collection of subagents in parallel; batching by 7 happens
    inside the action's `dispatches` array which the orchestrator can chunk.
    """
    dispatches = []
    for batch in batches:
        for job in batch:
            mid = job["matrix_id"]
            pid = job["principle_id"]
            lineage = job["interpretation_lineage"]
            dispatches.append({
                "subagent": "triz-principle-interpreter",
                "run_id": run_id,
                "expected_artifact": f"05_interpretation_{mid}_{pid}.json",
                "prompt": (
                    f"Interpret principle `{pid}` (canonical id "
                    f"`{job['canonical_id']}`) from matrix `{mid}` for the "
                    f"user's problem. Read the principle's name, description, "
                    f"and sub_principles from the matrix file. Apply lineage "
                    f"`{lineage}` (see triz-methodology skill for prompt "
                    f"variants). Write to "
                    f"`.triz/runs/{run_id}/05_interpretation_{mid}_{pid}.json` "
                    f"per 05_interpretation_single.schema.json."
                ),
            })
    return {
        "action": "dispatch_subagents_parallel",
        "run_id": run_id,
        "batch_size": INTERPRETER_BATCH_SIZE,
        "dispatches": dispatches,
    }


# --- Validation gate before each next-stage dispatch ---------------------

def _validate_artifact_or_diagnose(run_id: str, artifact_name: str) -> tuple[bool, str | None]:
    """Returns (ok, diagnostics)."""
    p = _common.run_dir(run_id, create=False) / artifact_name
    if not p.exists():
        return False, f"expected artifact missing: {artifact_name}"
    schema_name = _common.schema_for_artifact(artifact_name)
    if schema_name is None:
        return True, None  # No schema known — treat as opaque, trust filesystem.
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"invalid JSON in {artifact_name}: {e}"
    schema = _common.load_schema(schema_name)
    errs = sorted(jsonschema.Draft202012Validator(schema).iter_errors(data),
                  key=lambda e: list(e.absolute_path))
    if errs:
        first = errs[0]
        return False, (
            f"{artifact_name} schema violation at "
            f"{'/'.join(str(p) for p in first.absolute_path) or '<root>'}: "
            f"{first.message}"
        )
    return True, None


# --- Compatibility check (run once per session) ---------------------------

def _ensure_compatibility(state: dict) -> tuple[bool, str | None]:
    if state.get("compatibility_checked"):
        return True, None
    import subprocess
    script = _HERE / "compatibility_check.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--quiet"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception as e:
        return False, f"compatibility_check failed to run: {e}"
    if result.returncode != 0:
        return False, (
            (result.stderr.strip() or "compatibility_check failed")
            + f" (exit {result.returncode})"
        )
    state["compatibility_checked"] = True
    return True, None


# --- Main state machine ---------------------------------------------------

def _do_init(state: dict, args) -> int:
    """First call after --new-run: seed state, set FRAMER stage, emit framer dispatch."""
    text, flags = _parse_user_prompt(state.get("user_prompt", ""))
    state["flags"] = flags
    state["user_prompt"] = text
    state["max_loops"] = flags.get("max_loops", DEFAULT_MAX_LOOPS)
    _advance_stage(state, _common.Stage.FRAMER)
    _persist_state(state)
    return _emit(_action_run_framer(state["run_id"], text))


def _stage_framer(state: dict) -> int:
    run_id = state["run_id"]
    # Did the framer write 01_problem.json?
    ok, diag = _validate_artifact_or_diagnose(run_id, "01_problem.json")
    if not ok:
        retries = _bump_retry(state, "framer")
        _persist_state(state)
        if retries > MAX_RETRIES_PER_STAGE:
            return _emit_ask_user(
                "stage_retry_exhausted", run_id,
                stage_paused_at="framer",
                diagnostics=diag,
                options=[
                    {"id": "abort", "label": "Abort the run."},
                    {"id": "edit_artifact", "label": "Manually edit 01_problem.json then resume."},
                ],
            )
        return _emit(_action_run_framer(state["run_id"], state.get("user_prompt", "")))

    _advance_stage(state, _common.Stage.CHECK_FRAMING_CONFIDENCE)
    _persist_state(state)
    return _stage_check_framing_confidence(state)


def _stage_check_framing_confidence(state: dict) -> int:
    run_id = state["run_id"]
    problem = _common.read_artifact(run_id, "01_problem.json")
    conf = problem.get("framing_confidence")
    if conf == "low":
        return _emit_ask_user(
            "clarify_framing", run_id,
            stage_paused_at="01_problem",
            current_problem=problem,
            options=[
                {
                    "id": "accept_as_is",
                    "label": "Accept the framing as-is and proceed.",
                },
                {
                    "id": "provide_clarification",
                    "label": "Add clarification text to refine the framing.",
                    "prompts_user_for": "clarification_text",
                },
                {"id": "abort", "label": "Abort the run."},
            ],
        )
    _advance_stage(state, _common.Stage.SELECT_MATRIX)
    _persist_state(state)
    return _stage_select_matrix(state)


def _stage_select_matrix(state: dict) -> int:
    run_id = state["run_id"]
    flags = state.get("flags", {})
    overrides = list(flags.get("matrix_overrides", []) or [])
    overrides.extend(flags.get("matrices_overrides", []) or [])
    args = ["--run-id", run_id]
    for o in overrides:
        args.extend(["--matrix", o])
    return _emit({
        "action": "run_script",
        "script": "select_matrix.py",
        "args": args,
        "run_id": run_id,
        "expected_artifact": "02_selection.json",
    })


def _stage_after_selection(state: dict) -> int:
    """Called when 02_selection.json exists. Decides Stage E or moves on."""
    run_id = state["run_id"]
    ok, diag = _validate_artifact_or_diagnose(run_id, "02_selection.json")
    if not ok:
        retries = _bump_retry(state, "select_matrix")
        _persist_state(state)
        if retries > MAX_RETRIES_PER_STAGE:
            return _emit_ask_user(
                "stage_retry_exhausted", run_id,
                stage_paused_at="select_matrix",
                diagnostics=diag,
                options=[
                    {"id": "abort", "label": "Abort the run."},
                    {"id": "override_matrix", "label": "Force a matrix id.",
                     "prompts_user_for": "matrix_id"},
                ],
            )
        return _stage_select_matrix(state)

    selection = _common.read_artifact(run_id, "02_selection.json")
    if not selection.get("selected_matrices"):
        return _emit_ask_user(
            "no_matrices_selected", run_id,
            stage_paused_at="02_selection",
            rejected=selection.get("rejected_matrices", []),
            options=[
                {"id": "override_matrix", "label": "Force a matrix id.",
                 "prompts_user_for": "matrix_id"},
                {"id": "abandon_with_writeup",
                 "label": "Abandon and produce a no-resolution report."},
            ],
        )

    state["selected_matrices"] = [
        m["matrix_id"] for m in selection["selected_matrices"]
    ]
    _advance_stage(state, _common.Stage.STAGE_E_CHECK)
    _persist_state(state)
    return _stage_stage_e_check(state)


def _stage_stage_e_check(state: dict) -> int:
    run_id = state["run_id"]
    selection = _common.read_artifact(run_id, "02_selection.json")
    # If Stage E was invoked AND no LLM tiebreak ran yet (we infer via the
    # presence of a marker flag in state.flags), dispatch the selector subagent.
    flags = state.setdefault("flags", {})
    if selection.get("stage_e_invoked") and not flags.get("stage_e_completed"):
        flags["stage_e_completed"] = True
        _persist_state(state)
        return _emit(_action_run_selector_subagent(run_id))

    _advance_stage(state, _common.Stage.MAPPING_PHASE1)
    _persist_state(state)
    return _stage_mapping_phase1(state)


def _stage_mapping_phase1(state: dict) -> int:
    run_id = state["run_id"]
    selection = _common.read_artifact(run_id, "02_selection.json")
    problem = _common.read_artifact(run_id, "01_problem.json")
    flags = state.get("flags", {})
    no_critic = bool(flags.get("no_mapping_critic"))

    matrices = [m["matrix_id"] for m in selection.get("selected_matrices", [])]
    if not matrices:
        # Should not happen — _stage_after_selection guards.
        return _emit_self_correct(
            "no selected matrices when entering mapping_phase1"
        )

    # Already done? Check that all required artifacts exist.
    missing: list[str] = []
    for mid in matrices:
        if not _common.artifact_exists(run_id, f"03_mapping_{mid}.json"):
            missing.append(f"03_mapping_{mid}.json")
        if not no_critic and not _common.artifact_exists(run_id, f"03c_independent_mapping_{mid}.json"):
            missing.append(f"03c_independent_mapping_{mid}.json")
    if missing:
        # Dispatch all per-matrix mappers + critics in one parallel action.
        all_dispatches: list[dict] = []
        for mid in matrices:
            all_dispatches.extend(_action_mapper_and_critic_for(
                mid, run_id, problem, no_critic,
            ))
        return _emit({
            "action": "dispatch_subagents_parallel",
            "run_id": run_id,
            "dispatches": all_dispatches,
        })

    _advance_stage(state, _common.Stage.COMPARE_MAPPINGS)
    _persist_state(state)
    return _stage_compare_mappings(state)


def _stage_compare_mappings(state: dict) -> int:
    run_id = state["run_id"]
    selection = _common.read_artifact(run_id, "02_selection.json")
    flags = state.get("flags", {})
    no_critic = bool(flags.get("no_mapping_critic"))
    matrices = [m["matrix_id"] for m in selection.get("selected_matrices", [])]

    decisions: dict[str, str] = {}
    needs_phase2: list[str] = []
    no_clean: list[str] = []

    for mid in matrices:
        mapper = _common.read_artifact(run_id, f"03_mapping_{mid}.json")
        if no_critic:
            decisions[mid] = _common.Decision.AGREE.value
            continue
        try:
            crit = _common.read_artifact(run_id, f"03c_independent_mapping_{mid}.json")
        except FileNotFoundError:
            decisions[mid] = "MISSING_CRITIC"
            continue
        d = _compare_mappings(mapper, crit)
        decisions[mid] = d.value
        if d == _common.Decision.DISAGREE:
            needs_phase2.append(mid)
        elif d == _common.Decision.NO_CLEAN_MAPPING:
            no_clean.append(mid)

    state.setdefault("flags", {})["compare_decisions"] = decisions
    _persist_state(state)

    # If ALL matrices report no-clean-mapping, branch to no-resolution.
    if no_clean and len(no_clean) == len(matrices):
        state["flags"]["no_resolution"] = True
        _advance_stage(state, _common.Stage.ASSEMBLE)
        _persist_state(state)
        return _stage_assemble(state)

    if needs_phase2:
        # Dispatch Phase 2 critic for each disagreeing matrix.
        # Skip ones already done.
        remaining = [
            mid for mid in needs_phase2
            if not _common.artifact_exists(run_id, f"03b_mapping_critique_{mid}.json")
        ]
        if remaining:
            _advance_stage(state, _common.Stage.MAPPING_PHASE2)
            _persist_state(state)
            return _emit({
                "action": "dispatch_subagents_parallel",
                "run_id": run_id,
                "dispatches": [
                    {
                        "subagent": "triz-mapping-critic",
                        "run_id": run_id,
                        "expected_artifact": f"03b_mapping_critique_{mid}.json",
                        "prompt": _action_phase2_critic(mid, run_id)["prompt"],
                    }
                    for mid in remaining
                ],
            })
        # All Phase 2 critiques exist; fall through to lookup.

    # Drop any no_clean matrices from the active set so we only look up the
    # ones that survived. If everything dropped, the no_resolution branch
    # above handles it; otherwise we proceed with the survivors.
    active = [m for m in matrices if m not in no_clean]
    state.setdefault("flags", {})["active_matrices"] = active
    _advance_stage(state, _common.Stage.LOOKUP)
    _persist_state(state)
    return _stage_lookup(state)


def _stage_mapping_phase2(state: dict) -> int:
    """Reached after Phase 2 dispatches. Validates outputs, advances to lookup."""
    run_id = state["run_id"]
    selection = _common.read_artifact(run_id, "02_selection.json")
    matrices = [m["matrix_id"] for m in selection.get("selected_matrices", [])]
    decisions = state.get("flags", {}).get("compare_decisions", {})
    needs = [mid for mid, d in decisions.items() if d == _common.Decision.DISAGREE.value]
    missing = [mid for mid in needs
               if not _common.artifact_exists(run_id, f"03b_mapping_critique_{mid}.json")]
    if missing:
        retries = _bump_retry(state, "mapping_phase2")
        _persist_state(state)
        if retries > MAX_RETRIES_PER_STAGE:
            return _emit_ask_user(
                "stage_retry_exhausted", run_id,
                stage_paused_at="mapping_phase2",
                diagnostics=f"missing critiques for: {missing}",
                options=[{"id": "abort", "label": "Abort."}],
            )
        return _emit({
            "action": "dispatch_subagents_parallel",
            "run_id": run_id,
            "dispatches": [_action_phase2_critic(mid, run_id) | {"action": None}
                           for mid in missing],
        })

    # Move on.
    no_clean = [mid for mid, d in decisions.items()
                if d == _common.Decision.NO_CLEAN_MAPPING.value]
    active = [mid for mid in matrices if mid not in no_clean]
    state.setdefault("flags", {})["active_matrices"] = active
    _advance_stage(state, _common.Stage.LOOKUP)
    _persist_state(state)
    return _stage_lookup(state)


def _resolved_mapping_for(run_id: str, matrix_id: str) -> dict:
    """Pick the mapping the lookup script should consume.

    Phase 2 verdict (if present) overrides; otherwise the mapper's primary.
    """
    base = _common.read_artifact(run_id, f"03_mapping_{matrix_id}.json")
    p2_path = _common.run_dir(run_id, create=False) / f"03b_mapping_critique_{matrix_id}.json"
    if p2_path.exists():
        with open(p2_path, "r", encoding="utf-8") as f:
            verdict = json.load(f)
        if verdict.get("verdict") in {"disagree", "propose_third"}:
            chosen = verdict.get("chosen_mapping") or {}
            base = dict(base)
            if chosen.get("improving_param_id"):
                base["improving_param_id"] = chosen["improving_param_id"]
            if chosen.get("worsening_param_id"):
                base["worsening_param_id"] = chosen["worsening_param_id"]
    return base


def _stage_lookup(state: dict) -> int:
    run_id = state["run_id"]
    flags = state.setdefault("flags", {})
    active = flags.get("active_matrices") or state.get("selected_matrices", [])

    # For each active matrix, write the resolved mapping (in case Phase 2
    # changed it) so lookup_principles.py reads the right data, then dispatch
    # the lookups in sequence. Lookups are deterministic scripts; we run them
    # one per state-driver iteration so each gets validated independently.
    pending = [m for m in active
               if not _common.artifact_exists(run_id, f"04_principles_{m}.json")]
    if pending:
        nxt = pending[0]
        # Ensure the mapping artifact lookup_principles reads is the resolved one.
        resolved = _resolved_mapping_for(run_id, nxt)
        _common.write_artifact(run_id, f"03_mapping_{nxt}.json", resolved)
        return _emit(_action_lookup_for(nxt, run_id))

    # All lookups done. Check no-clean-mapping cascade.
    populated_any = False
    for m in active:
        try:
            data = _common.read_artifact(run_id, f"04_principles_{m}.json")
            if data.get("populated"):
                populated_any = True
        except Exception:
            continue
    if not populated_any:
        flags["no_resolution"] = True
        _advance_stage(state, _common.Stage.ASSEMBLE)
        _persist_state(state)
        return _stage_assemble(state)

    _advance_stage(state, _common.Stage.INTERPRET)
    _persist_state(state)
    return _stage_interpret(state)


def _stage_interpret(state: dict) -> int:
    run_id = state["run_id"]
    flags = state.setdefault("flags", {})
    active = flags.get("active_matrices") or state.get("selected_matrices", [])

    # Build the per-(matrix, principle) job list, only for principles where
    # the per-principle interpretation file doesn't already exist.
    jobs: list[dict] = []
    for mid in active:
        try:
            principles = _common.read_artifact(run_id, f"04_principles_{mid}.json")
        except FileNotFoundError:
            continue
        if not principles.get("populated"):
            continue
        # Look up canonical_id and lineage from the matrix file.
        try:
            matrix = _common.load_matrix(mid)
        except Exception:
            continue
        meta = matrix.get("meta") or {}
        lineage = meta.get("interpretation_lineage", "altshuller-40")
        ptable = matrix.get("principles") or {}
        for pid in principles.get("principles", []):
            spid = str(pid)
            artifact = f"05_interpretation_{mid}_{spid}.json"
            if _common.artifact_exists(run_id, artifact):
                continue
            entry = ptable.get(spid) or {}
            canonical = entry.get("canonical_id") or f"P_UNKNOWN_{spid}"
            jobs.append({
                "matrix_id": mid,
                "principle_id": spid,
                "canonical_id": canonical,
                "interpretation_lineage": lineage,
            })

    if jobs:
        # Chunk into batches of INTERPRETER_BATCH_SIZE. The state-driver emits
        # one parallel-dispatch action per call; batching lets the orchestrator
        # cap parallelism. Here we emit them all and let the orchestrator
        # respect batch_size.
        batches = [jobs[i:i + INTERPRETER_BATCH_SIZE]
                   for i in range(0, len(jobs), INTERPRETER_BATCH_SIZE)]
        return _emit(_action_interpret(run_id, batches))

    _advance_stage(state, _common.Stage.MERGE_INTERPRETATIONS)
    _persist_state(state)
    return _stage_merge(state)


def _stage_merge(state: dict) -> int:
    run_id = state["run_id"]
    if not _common.artifact_exists(run_id, "05_interpretations.json"):
        return _emit({
            "action": "run_script",
            "script": "merge_interpretations.py",
            "args": ["--run-id", run_id],
            "run_id": run_id,
            "expected_artifact": "05_interpretations.json",
        })
    _advance_stage(state, _common.Stage.SYNTHESIZE)
    _persist_state(state)
    return _stage_synthesize(state)


def _stage_synthesize(state: dict) -> int:
    run_id = state["run_id"]
    if not _common.artifact_exists(run_id, "06_solutions.json"):
        return _emit({
            "action": "dispatch_subagent",
            "subagent": "triz-solution-synthesizer",
            "run_id": run_id,
            "expected_artifact": "06_solutions.json",
            "prompt": (
                f"Synthesize 1-4 candidate solutions for run `{run_id}`. Read "
                f"`.triz/runs/{run_id}/01_problem.json` and "
                f"`.triz/runs/{run_id}/05_interpretations.json`. Per design v6 "
                f"§9.6a: principles_applied is deduped on canonical_id; "
                f"interpretation_refs preserves every contributing "
                f"interpretation including multiple from the same canonical_id "
                f"with different interpretation_lineages. Write to "
                f"`.triz/runs/{run_id}/06_solutions.json` per "
                f"06_solutions.schema.json."
            ),
        })

    if state.get("flags", {}).get("no_critique"):
        # Skip critique entirely.
        _advance_stage(state, _common.Stage.ASSEMBLE)
        _persist_state(state)
        return _stage_assemble(state)

    _advance_stage(state, _common.Stage.CRITIQUE)
    _persist_state(state)
    return _stage_critique(state)


def _stage_critique(state: dict) -> int:
    run_id = state["run_id"]
    if not _common.artifact_exists(run_id, "07_critique.json"):
        return _emit({
            "action": "dispatch_subagent",
            "subagent": "triz-contradiction-critic",
            "run_id": run_id,
            "expected_artifact": "07_critique.json",
            "prompt": (
                f"Critique each candidate in "
                f"`.triz/runs/{run_id}/06_solutions.json`. For each, list "
                f"secondary contradictions, set severity (minor/moderate/severe/fatal), "
                f"enumerate risks, and provide a recommendation. Write to "
                f"`.triz/runs/{run_id}/07_critique.json` per 07_critique.schema.json."
            ),
        })
    _advance_stage(state, _common.Stage.CHECK_FATAL_SEVERITY)
    _persist_state(state)
    return _stage_check_fatal(state)


def _stage_check_fatal(state: dict) -> int:
    run_id = state["run_id"]
    critique = _common.read_artifact(run_id, "07_critique.json")
    crits = critique.get("per_solution_critiques", [])
    fatal = [c for c in crits if c.get("severity") == "fatal"]
    if not fatal:
        _advance_stage(state, _common.Stage.ASSEMBLE)
        _persist_state(state)
        return _stage_assemble(state)

    all_fatal = len(fatal) == len(crits)
    options: list[dict] = []
    if not all_fatal:
        # drop_fatal_proceed only makes sense when some non-fatal candidates
        # survive. Per design v6 §17.3 it's gated to some_fatal.
        options.append({
            "id": "drop_fatal_proceed",
            "label": "Drop the fatal candidate(s); proceed with the others.",
            "available_when": "some_fatal",
        })
    options.extend([
        {"id": "reformulate_with_constraint",
         "label": "Add a constraint to the original problem and re-run synthesis.",
         "prompts_user_for": "constraint_text"},
        {"id": "try_different_matrix",
         "label": "Re-run with a different matrix (override auto-selection).",
         "prompts_user_for": "matrix_id"},
        {"id": "accept_with_override",
         "label": "Accept the fatal candidate anyway (logged as explicit override)."},
        # abandon_with_writeup available on BOTH some_fatal and all_fatal
        # (v6 §17.3 corrected v5 which restricted to all_fatal).
        {"id": "abandon_with_writeup",
         "label": "Abandon the run; produce a 'no acceptable resolution' report."},
    ])
    return _emit_ask_user(
        "fatal_severity_in_critique", run_id,
        stage_paused_at="07_critique",
        fatal_candidates=[c["candidate_name"] for c in fatal],
        non_fatal_candidates=[c["candidate_name"] for c in crits if c.get("severity") != "fatal"],
        options=options,
    )


def _stage_assemble(state: dict) -> int:
    run_id = state["run_id"]
    flags = state.get("flags", {})
    args = ["--run-id", run_id]
    if flags.get("no_resolution"):
        args.append("--no_resolution")
    if flags.get("override_logged"):
        args.append("--override_logged")
    for ex in flags.get("excluded_candidates", []) or []:
        args.extend(["--exclude", ex])
    rd = _common.run_dir(run_id, create=False)
    if not (rd / "final-report.md").exists():
        return _emit({
            "action": "run_script",
            "script": "assemble_report.py",
            "args": args,
            "run_id": run_id,
            "expected_artifact": "final-report.md",
        })
    _advance_stage(state, _common.Stage.DONE)
    _persist_state(state)
    return _emit_done(run_id, str(rd / "final-report.md"))


# --- User decision application -------------------------------------------

def _apply_user_decision(state: dict, raw: str) -> tuple[bool, str | None]:
    """Apply --user-input. Returns (ok, error)."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, f"--user-input is not valid JSON: {e}"
    choice = payload.get("choice")
    if not choice:
        return False, "--user-input missing 'choice'"

    flags = state.setdefault("flags", {})

    if choice == "abort":
        # Mark for abandonment via assemble + no_resolution.
        flags["no_resolution"] = True
        state["current_stage"] = _common.Stage.ASSEMBLE.value
        return True, None

    if choice == "accept_as_is":
        # Continue framing → selection.
        state["current_stage"] = _common.Stage.SELECT_MATRIX.value
        return True, None

    if choice == "provide_clarification":
        # Append clarification to constraints and re-run framer.
        text = payload.get("clarification_text", "").strip()
        if text:
            try:
                problem = _common.read_artifact(state["run_id"], "01_problem.json")
                problem.setdefault("constraints", []).append(
                    f"Clarification: {text}"
                )
                _common.write_artifact(state["run_id"], "01_problem.json", problem)
            except Exception:
                pass
        state["current_stage"] = _common.Stage.FRAMER.value
        return True, None

    if choice == "override_matrix":
        mid = payload.get("matrix_id", "").strip()
        if not mid:
            return False, "override_matrix requires matrix_id"
        flags.setdefault("matrix_overrides", []).append(mid)
        # Reset selection.
        rd = _common.run_dir(state["run_id"], create=False)
        for stale in ("02_selection.json",):
            p = rd / stale
            if p.exists():
                p.unlink()
        state["current_stage"] = _common.Stage.SELECT_MATRIX.value
        return True, None

    if choice == "drop_fatal_proceed":
        # Caller usually supplies fatal_candidates; if not, derive from critique.
        excluded = payload.get("fatal_candidates")
        if not excluded:
            try:
                crit = _common.read_artifact(state["run_id"], "07_critique.json")
                excluded = [c["candidate_name"]
                            for c in crit.get("per_solution_critiques", [])
                            if c.get("severity") == "fatal"]
            except Exception:
                excluded = []
        flags["excluded_candidates"] = excluded
        state["current_stage"] = _common.Stage.ASSEMBLE.value
        return True, None

    if choice == "reformulate_with_constraint":
        text = payload.get("constraint_text", "").strip()
        if not text:
            return False, "reformulate_with_constraint requires constraint_text"
        try:
            problem = _common.read_artifact(state["run_id"], "01_problem.json")
            problem.setdefault("constraints", []).append(text)
            _common.write_artifact(state["run_id"], "01_problem.json", problem)
        except Exception:
            pass
        # Reset to synthesize: keep selection + mapping + lookups, but redo
        # synthesis with the new constraint. Drop downstream artifacts.
        rd = _common.run_dir(state["run_id"], create=False)
        for stale in ("06_solutions.json", "07_critique.json", "final-report.md"):
            p = rd / stale
            if p.exists():
                p.unlink()
        state["current_stage"] = _common.Stage.SYNTHESIZE.value
        return True, None

    if choice == "try_different_matrix":
        mid = payload.get("matrix_id", "").strip()
        if not mid:
            return False, "try_different_matrix requires matrix_id"
        flags.setdefault("matrix_overrides", []).append(mid)
        rd = _common.run_dir(state["run_id"], create=False)
        # Wipe everything from selection downward.
        for p in rd.glob("0*.json"):
            if p.name == "01_problem.json":
                continue
            p.unlink()
        for p in rd.glob("final-report.md"):
            p.unlink()
        state["current_stage"] = _common.Stage.SELECT_MATRIX.value
        return True, None

    if choice == "accept_with_override":
        flags["override_logged"] = True
        state["current_stage"] = _common.Stage.ASSEMBLE.value
        return True, None

    if choice == "abandon_with_writeup":
        flags["no_resolution"] = True
        state["current_stage"] = _common.Stage.ASSEMBLE.value
        return True, None

    if choice == "edit_artifact":
        # Caller will edit the file out-of-band; we just resume from the
        # current stage which will re-validate.
        return True, None

    return False, f"unknown user decision choice: {choice!r}"


# --- Stage dispatch table ------------------------------------------------

def _dispatch(state: dict) -> int:
    """Dispatch on state.current_stage. Each handler may advance and recurse."""
    stage = state.get("current_stage")
    if stage == _common.Stage.INIT.value:
        # Should only happen on a fresh state with no prior framer run.
        text, _ = _parse_user_prompt(state.get("user_prompt", ""))
        return _emit(_action_run_framer(state["run_id"], text))
    if stage == _common.Stage.FRAMER.value:
        return _stage_framer(state)
    if stage == _common.Stage.CHECK_FRAMING_CONFIDENCE.value:
        return _stage_check_framing_confidence(state)
    if stage == _common.Stage.SELECT_MATRIX.value:
        # If 02_selection.json exists, treat this iteration as post-selection.
        if _common.artifact_exists(state["run_id"], "02_selection.json"):
            return _stage_after_selection(state)
        return _stage_select_matrix(state)
    if stage == _common.Stage.STAGE_E_CHECK.value:
        return _stage_stage_e_check(state)
    if stage == _common.Stage.MAPPING_PHASE1.value:
        return _stage_mapping_phase1(state)
    if stage == _common.Stage.COMPARE_MAPPINGS.value:
        return _stage_compare_mappings(state)
    if stage == _common.Stage.MAPPING_PHASE2.value:
        return _stage_mapping_phase2(state)
    if stage == _common.Stage.LOOKUP.value:
        return _stage_lookup(state)
    if stage == _common.Stage.INTERPRET.value:
        return _stage_interpret(state)
    if stage == _common.Stage.MERGE_INTERPRETATIONS.value:
        return _stage_merge(state)
    if stage == _common.Stage.SYNTHESIZE.value:
        return _stage_synthesize(state)
    if stage == _common.Stage.CRITIQUE.value:
        return _stage_critique(state)
    if stage == _common.Stage.CHECK_FATAL_SEVERITY.value:
        return _stage_check_fatal(state)
    if stage == _common.Stage.ASSEMBLE.value:
        return _stage_assemble(state)
    if stage == _common.Stage.DONE.value:
        rd = _common.run_dir(state["run_id"], create=False)
        return _emit_done(state["run_id"], str(rd / "final-report.md"))
    return _emit_self_correct(f"unknown stage: {stage!r}")


# --- main() ---------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args, parse_err = _parse_args_safely(argv)
    if parse_err is not None:
        return _emit_self_correct(
            f"argparse: {parse_err}",
            hint="usage: next_action.py [--new-run --user-prompt <text>] | "
                 "[--run-id <id> [--user-input <json>]]",
        )

    try:
        # Resolve run_id: either passed in, or generated for --new-run.
        if args.new_run:
            run_id = args.run_id or (
                f"run-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
            )
            state = _new_state(run_id, args.user_prompt or "")
            ok, err = _ensure_compatibility(state)
            if not ok:
                return _emit_ask_user(
                    "compatibility_failed", run_id,
                    diagnostics=err,
                    options=[
                        {"id": "abort", "label": "Abort the run."},
                    ],
                )
            _persist_state(state)
            return _do_init(state, args)

        if not args.run_id:
            return _emit_self_correct(
                "missing --run-id (and not --new-run)",
                hint="pass --run-id <id> for an existing run, or "
                     "--new-run --user-prompt <text> to start one",
            )

        try:
            state = _load_state(args.run_id)
        except FileNotFoundError:
            return _emit_self_correct(
                f"no state.json for run_id={args.run_id!r}",
                hint="start a new run with --new-run --user-prompt <text>",
            )
        except json.JSONDecodeError as e:
            return _emit_ask_user(
                "state_corrupted", args.run_id,
                diagnostics=f"state.json not parseable: {e}",
                options=[
                    {"id": "abort", "label": "Abort the run."},
                    {"id": "attempt_repair",
                     "label": "Attempt to repair state.json (manual edit)."},
                ],
            )

        # Run compatibility check once per session.
        ok, err = _ensure_compatibility(state)
        if not ok:
            _persist_state(state)
            return _emit_ask_user(
                "compatibility_failed", state["run_id"],
                diagnostics=err,
                options=[{"id": "abort", "label": "Abort the run."}],
            )
        _persist_state(state)

        if args.user_input:
            ok, err = _apply_user_decision(state, args.user_input)
            if not ok:
                return _emit_self_correct(
                    f"user input rejected: {err}",
                    hint='--user-input must be a JSON object with at least {"choice": "..."}',
                )
            _persist_state(state)

        return _dispatch(state)

    except Exception as e:
        # Top-level safety net per design v6 §19.2: convert any exception
        # into a self_correct so the orchestrator can recover.
        return _emit_self_correct(
            f"internal error: {type(e).__name__}: {e}",
            hint="re-invoke next_action.py; if persistent, inspect state.json manually",
        )


if __name__ == "__main__":
    # Strict CLI contract: exit code is ALWAYS 0; stderr is ALWAYS empty.
    # The one exception is `--help`, which is developer-facing and lets
    # argparse print to stdout and exit 0 normally.
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        # Let argparse handle the help flow with its normal output.
        sys.exit(main())

    try:
        # Suppress any stray stderr so the contract holds even if a deep
        # import logs warnings.
        with redirect_stderr(io.StringIO()):
            main()
    except SystemExit:
        # argparse hardening should have prevented this; but if it slips
        # through, emit self_correct and exit 0.
        sys.stdout.write(json.dumps({
            "action": "self_correct",
            "message": "argparse hardening bypass; SystemExit raised",
        }) + "\n")
    except Exception as e:
        sys.stdout.write(json.dumps({
            "action": "self_correct",
            "message": f"unhandled top-level exception: {type(e).__name__}: {e}",
        }) + "\n")
    sys.exit(0)
