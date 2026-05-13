#!/usr/bin/env python3
"""assemble_report.py — render final-report.md from the run's artifacts.

Per design v6 §10.7 + §16:
- Reads 0N_*.json artifacts from the run dir.
- Pure formatting; NO LLM call.
- --no_resolution emits the §16 no-clean-mapping template.
- --exclude=<candidate-name> drops a candidate (used by drop_fatal_proceed
  in the fatal-severity flow).
- --override_logged stamps the report with the explicit-override note
  (used by accept_with_override).

Output: final-report.md in the run dir.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402


# Altshuller-39 parameter groups, used for the no-resolution template's
# "neighborhood-suggestive principles" section. Per design v6 §16 the source
# is matrix_storage_design's meta_analysis.md; if a non-Altshuller matrix
# declares its own groups via meta.parameter_groups we honor those instead.
_ALTSHULLER_GROUPS: dict[str, list[int]] = {
    "physical_geometry_1_8": list(range(1, 9)),
    "mechanical_9_14": list(range(9, 15)),
    "temporal_durability_15_16": [15, 16],
    "energy_thermal_17_22": list(range(17, 23)),
    "loss_quantity_23_26": list(range(23, 27)),
    "quality_system_27_31": list(range(27, 32)),
    "usability_manufacturing_32_39": list(range(32, 40)),
}


def _safe_load(run_id: str, name: str) -> dict | None:
    try:
        return _common.read_artifact(run_id, name)
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _list_mappings(run_id: str) -> list[dict]:
    rd = _common.run_dir(run_id, create=False)
    out = []
    for p in sorted(rd.glob("03_mapping_*.json")):
        if p.name.startswith("03b_") or p.name.startswith("03c_"):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


def _list_independent(run_id: str) -> list[dict]:
    rd = _common.run_dir(run_id, create=False)
    out = []
    for p in sorted(rd.glob("03c_independent_mapping_*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


def _list_principles(run_id: str) -> list[dict]:
    rd = _common.run_dir(run_id, create=False)
    out = []
    for p in sorted(rd.glob("04_principles_*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out


def _principle_group(matrix_id: str, principle_ids: list[int]) -> dict[str, list[int]]:
    """Group ids by Altshuller-39 buckets when the matrix uses that taxonomy."""
    try:
        matrix = _common.load_matrix(matrix_id)
        meta = matrix.get("meta") or {}
        groups = meta.get("parameter_groups")
        if not groups:
            tax = meta.get("principle_taxonomy", "")
            if tax in {"altshuller-40", "biotriz-40"}:
                groups = _ALTSHULLER_GROUPS
        if not groups:
            return {}
    except Exception:
        return {}
    out: dict[str, list[int]] = {}
    pset = set(principle_ids)
    for name, members in groups.items():
        hits = [m for m in members if m in pset]
        if hits:
            out[name] = hits
    return out


def _bullets(items: list[str], indent: str = "") -> str:
    return "\n".join(f"{indent}- {x}" for x in items) if items else f"{indent}- (none)"


def _render_problem(problem: dict | None) -> list[str]:
    if not problem:
        return ["## Problem", "", "_(01_problem.json missing)_", ""]
    lines = ["## Problem", ""]
    lines.append(f"- **Improving:** {problem.get('improving_concept','?')}")
    lines.append(f"- **Worsening:** {problem.get('worsening_concept','?')}")
    lines.append(f"- **Contradiction type:** {problem.get('contradiction_type','?')}")
    lines.append(f"- **Domain class:** {problem.get('domain_class','?')}")
    lines.append(f"- **Framing confidence:** {problem.get('framing_confidence','?')}")
    if problem.get("domain_signals"):
        lines.append(f"- **Domain signals:** {', '.join(problem['domain_signals'])}")
    if problem.get("exotic_signals"):
        lines.append(f"- **Exotic signals:** {', '.join(problem['exotic_signals'])}")
    if problem.get("constraints"):
        lines.append("- **Constraints:**")
        for c in problem["constraints"]:
            lines.append(f"  - {c}")
    if problem.get("rationale"):
        lines.extend(["", f"_{problem['rationale']}_"])
    lines.append("")
    return lines


def _render_selection(selection: dict | None) -> list[str]:
    if not selection:
        return ["## Matrix Selection", "", "_(02_selection.json missing)_", ""]
    lines = ["## Matrix Selection", ""]
    lines.append(f"- **Strategy:** {selection.get('run_strategy','?')}")
    lines.append(f"- **Weights version:** {selection.get('weights_version','?')}")
    lines.append(f"- **Stage E invoked:** {selection.get('stage_e_invoked', False)}")
    lines.append("")
    lines.append("### Selected matrices")
    for m in selection.get("selected_matrices", []):
        lines.append(
            f"- **{m['matrix_id']}** "
            f"(score {m['score']:.1f}, confidence {m['selection_confidence']})"
        )
        lines.append(f"  - {m.get('rationale','')}")
    lines.append("")
    return lines


def _render_synth_section(
    solutions: dict | None,
    critique: dict | None,
    interpretations: dict | None,
    excluded: set[str],
    override_logged: bool,
) -> list[str]:
    lines = ["## Candidate Solutions", ""]
    if not solutions:
        lines.append("_(06_solutions.json missing)_")
        lines.append("")
        return lines

    crits_by_name: dict[str, dict] = {}
    if critique:
        for c in critique.get("per_solution_critiques", []):
            crits_by_name[c["candidate_name"]] = c

    interp_by_ref: dict[tuple[str, str], dict] = {}
    if interpretations:
        for e in interpretations.get("interpretations", []):
            key = (e.get("matrix_id", ""), str(e.get("principle_id", "")))
            interp_by_ref[key] = e

    candidates = solutions.get("candidates", [])
    rendered = 0
    for idx, cand in enumerate(candidates):
        # excluded may contain free-text names OR stable ordinal ids ("s1",
        # "s2", ...). Either form drops the candidate.
        solution_id = f"s{idx + 1}"
        if cand.get("name") in excluded or solution_id in excluded:
            continue
        rendered += 1
        lines.append(f"### Candidate: {cand['name']}")
        if override_logged:
            lines.append(
                "> NOTE: This run includes an explicit user override "
                "(`accept_with_override`). A prior critique flagged a fatal-"
                "severity concern."
            )
        lines.append("")
        lines.append(f"{cand.get('summary','')}")
        lines.append("")
        lines.append(
            f"- **Novelty:** {cand.get('novelty_estimate','?')} | "
            f"**Effort:** {cand.get('effort_estimate','?')}"
        )
        lines.append(
            f"- **Principles applied:** "
            f"{', '.join(cand.get('principles_applied', [])) or '(none)'}"
        )
        lines.append("")
        lines.append("**Implementation sketch.**")
        lines.append("")
        lines.append(cand.get("implementation_sketch", ""))
        lines.append("")

        # Cross-matrix angles: list every interpretation_ref so two angles on
        # the same canonical_id stay distinct (design v6 §9.6a).
        refs = cand.get("interpretation_refs", [])
        if refs:
            lines.append("**Interpretations contributing:**")
            for ref in refs:
                key = (ref.get("matrix_id", ""), str(ref.get("principle_id", "")))
                e = interp_by_ref.get(key)
                if e:
                    lineage = e.get("interpretation_lineage", "?")
                    name = e.get("principle_name", "?")
                    sug = e.get("concrete_suggestion", "")
                    lines.append(
                        f"- _{lineage}_ on **{name}** ({key[0]}): {sug}"
                    )
                else:
                    lines.append(
                        f"- _(missing interpretation for {key})_"
                    )
            lines.append("")

        crit = crits_by_name.get(cand["name"])
        if crit:
            lines.append("**Critique.**")
            lines.append("")
            lines.append(f"- **Severity:** {crit.get('severity','?')}")
            lines.append(f"- **Recommendation:** {crit.get('recommendation','')}")
            sec = crit.get("secondary_contradictions", [])
            if sec:
                lines.append("- **Secondary contradictions:**")
                for s in sec:
                    lines.append(
                        f"  - {s.get('improving','?')} ⇄ {s.get('worsening','?')} "
                        f"({s.get('severity','?')})"
                    )
            risks = crit.get("risks", [])
            if risks:
                lines.append("- **Risks:**")
                for r in risks:
                    lines.append(f"  - {r}")
            lines.append("")

    if rendered == 0:
        lines.append("_(all candidates excluded by --exclude)_")
        lines.append("")
    return lines


def _render_no_resolution(
    problem: dict | None,
    selection: dict | None,
    mappings: list[dict],
    independents: list[dict],
    principles: list[dict],
) -> list[str]:
    lines = ["# TRIZ Workshop Report (No Clean Resolution)", ""]
    lines.append(
        "> This contradiction is not standardly resolved by the selected matrix/matrices. "
        "Per Souchkov's empirical finding (~10-15% clean-mapping rate), this is an "
        "expected output, not an error. Consider problem reformulation, ARIZ, or a "
        "different methodology."
    )
    lines.append("")
    lines.extend(_render_problem(problem))
    lines.extend(_render_selection(selection))

    # Closest mapper attempts (mapper primary + first alternative, plus critic
    # independent attempt).
    lines.append("## Closest Parameter Pairs Considered")
    lines.append("")
    if mappings:
        for m in mappings:
            lines.append(f"### Mapper on `{m.get('matrix_id','?')}`")
            lines.append(
                f"- **Primary:** ({m.get('improving_param_id','?')}, "
                f"{m.get('worsening_param_id','?')}) — "
                f"confidence {m.get('mapping_confidence','?')}"
            )
            for alt in m.get("alternatives", [])[:2]:
                lines.append(
                    f"- **Alt:** ({alt.get('improving_param_id','?')}, "
                    f"{alt.get('worsening_param_id','?')}) — "
                    f"strength {alt.get('alt_strength','?')}"
                )
            lines.append("")
    else:
        lines.append("_(no 03_mapping_*.json files)_")
        lines.append("")

    if independents:
        lines.append("### Critic independent mappings")
        for ic in independents:
            lines.append(
                f"- **{ic.get('matrix_id','?')}**: "
                f"({ic.get('improving_param_id','?')}, "
                f"{ic.get('worsening_param_id','?')}) — "
                f"confidence {ic.get('confidence','?')}"
            )
        lines.append("")

    # Neighborhood-suggestive principles.
    lines.append("## Neighborhood-Suggestive Principles")
    lines.append("")
    lines.append(
        "_The cells the mapper considered are empty. The principles below come "
        "from cells that share a parameter group with the mapper's pair. They "
        "are NOT a direct lookup — they're suggestive only._"
    )
    lines.append("")
    if principles:
        for pp in principles:
            mid = pp.get("matrix_id", "?")
            tried = pp.get("alternatives_tried", [])
            collected: list[int] = []
            for t in tried:
                # Walk the cells we attempted; for each one, gather principles
                # from cells that share a parameter group with the attempt.
                imp = t.get("improving_param_id", "")
                try:
                    imp_int = int(imp)
                except (TypeError, ValueError):
                    continue
                # Only Altshuller-style numeric ids are grouped today.
                # If grouping returned principles via the matrix file, surface
                # them; this is intentionally a lightweight lookup.
                grouped = _principle_group(mid, [imp_int])
                if grouped:
                    for grp in grouped:
                        collected.append(imp_int)
            collected = sorted(set(collected))
            lines.append(f"- **{mid}**: parameter-group neighbors of attempted "
                         f"axes: {collected if collected else '(none in known groups)'}")
        lines.append("")
    else:
        lines.append("_(no 04_principles_*.json files; no neighborhood data available)_")
        lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append(
        "- Reformulate the problem (try a different improving/worsening framing).\n"
        "- Consider ARIZ for problems where the contradiction matrix is too coarse.\n"
        "- Try `/prizm:replay <run-id> --use-current-registry` if "
        "the corpus has been updated.\n"
        "- Override matrix selection: `/prizm:solve \"...\" --matrix=<id>`."
    )
    lines.append("")
    return lines


def assemble(
    run_id: str,
    excluded: set[str],
    no_resolution: bool,
    override_logged: bool,
) -> str:
    problem = _safe_load(run_id, "01_problem.json")
    selection = _safe_load(run_id, "02_selection.json")
    interpretations = _safe_load(run_id, "05_interpretations.json")
    solutions = _safe_load(run_id, "06_solutions.json")
    critique = _safe_load(run_id, "07_critique.json")
    mappings = _list_mappings(run_id)
    independents = _list_independent(run_id)
    principles = _list_principles(run_id)

    if no_resolution:
        body = _render_no_resolution(
            problem, selection, mappings, independents, principles,
        )
        return "\n".join(body)

    lines: list[str] = [
        f"# TRIZ Workshop Report — run `{run_id}`",
        "",
    ]
    lines.extend(_render_problem(problem))
    lines.extend(_render_selection(selection))
    lines.extend(_render_synth_section(
        solutions, critique, interpretations, excluded, override_logged,
    ))

    # Trace footer for auditability.
    lines.append("---")
    lines.append("")
    lines.append("## Trace")
    lines.append("")
    rd = _common.run_dir(run_id, create=False)
    top_artifacts = sorted(p.name for p in rd.glob("0*.json"))
    partial_dir = rd / "partial"
    partial_artifacts = sorted(p.name for p in partial_dir.glob("*.json")) \
        if partial_dir.exists() else []
    total = len(top_artifacts) + len(partial_artifacts)
    lines.append(f"- **Run dir:** `{rd}`")
    lines.append(f"- **Artifacts:** {total} "
                 f"(top-level {len(top_artifacts)}, "
                 f"partial/ {len(partial_artifacts)})")
    for a in top_artifacts:
        lines.append(f"  - {a}")
    for a in partial_artifacts:
        lines.append(f"  - partial/{a}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="assemble_report.py",
        description="Assemble final-report.md from the run's artifacts. "
                    "Pure formatting, no LLM.",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--exclude", action="append", default=None,
        help="Candidate name to exclude. May be passed multiple times "
             "(used by drop_fatal_proceed).",
    )
    parser.add_argument(
        "--no_resolution", action="store_true",
        help="Use the no-clean-mapping template (design v6 §16).",
    )
    parser.add_argument(
        "--override_logged", action="store_true",
        help="Stamp the report with the accept_with_override note.",
    )
    args = parser.parse_args(argv)

    excluded = set(args.exclude or [])
    try:
        text = assemble(args.run_id, excluded, args.no_resolution, args.override_logged)
    except Exception as e:
        print(f"assemble_report: failed: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 2

    rd = _common.run_dir(args.run_id)
    out = rd / "final-report.md"
    # final-report.md is markdown, not a schema-validated artifact.
    _common.atomic_write(out, text, validate=False)
    print(f"assemble_report: wrote {out} ({len(text.splitlines())} lines)")

    # Render the HTML digest as a sibling artifact. Failure here is logged
    # but does not fail the run — the markdown report is the authoritative
    # output; digest.html is a visual convenience.
    try:
        import generate_digest
        digest_text = generate_digest.render_digest(
            args.run_id, excluded, args.override_logged,
        )
        digest_out = rd / "digest.html"
        _common.atomic_write(digest_out, digest_text, validate=False)
        print(f"assemble_report: wrote {digest_out} "
              f"({len(digest_text)} bytes)")
    except Exception as e:
        print(f"assemble_report: digest generation failed "
              f"({type(e).__name__}: {e}); final-report.md is unaffected",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"assemble_report: internal error: {type(e).__name__}: {e}",
              file=sys.stderr)
        sys.exit(2)
