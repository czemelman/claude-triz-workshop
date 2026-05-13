#!/usr/bin/env python3
"""generate_digest.py — render digest.html for a prizm run.

Visual companion to final-report.md. Self-contained HTML (inline CSS, no JS,
no external assets) so it opens cleanly from the filesystem. Adapted from
the brainstorm/storm digest aesthetic (dark theme, stat cards, pipeline
strip, severity-coded sections, collapsible details).

Usage:
    python3 generate_digest.py --run-id <id> [--exclude <name|sX>]...

Reads artifacts from .triz/runs/<run_id>/ and writes digest.html next to
final-report.md. Pure formatting; no LLM calls.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _common  # noqa: E402


# --- Palette (Storm-style dark theme) ------------------------------------

SEVERITY_COLORS = {
    "minor":    ("#1e293b", "#bbf7d0", "#166534"),  # bg, text, border
    "moderate": ("#1e293b", "#fef08a", "#854d0e"),
    "severe":   ("#1e293b", "#fed7aa", "#9a3412"),
    "fatal":    ("#1e293b", "#fca5a5", "#7f1d1d"),
}

FRAMING_COLORS = {
    "high":   "#10b981",
    "medium": "#f59e0b",
    "low":    "#ef4444",
}

VERDICT_COLORS = {
    "agree":         ("#bbf7d0", "#166534"),
    "disagree":      ("#fed7aa", "#9a3412"),
    "propose_third": ("#c7d2fe", "#312e81"),
}


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def _safe_load(run_id: str, name: str):
    try:
        return _common.read_artifact(run_id, name)
    except Exception:
        return None


def _glob_load(run_id: str, pattern: str) -> list[dict]:
    rd = _common.run_dir(run_id, create=False)
    out: list[dict] = []
    for p in sorted(rd.glob(pattern)):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            d["__path"] = p.name
            out.append(d)
        except Exception:
            continue
    return out


# --- CSS (inlined) -------------------------------------------------------

_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
       background: #0f172a; color: #e2e8f0; line-height: 1.6;
       padding: 2rem; max-width: 1100px; margin: 0 auto; }
h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; font-weight: 600; color: #94a3b8; margin-bottom: 1rem;
     text-transform: uppercase; letter-spacing: 0.05em; }
h3 { font-size: 1rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.5rem; }
.subtitle { font-size: 1rem; color: #94a3b8; margin-bottom: 1rem; }
.meta-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
.meta-badge { padding: 0.25rem 0.75rem; border-radius: 9999px;
              font-size: 0.8rem; font-weight: 600;
              background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
.meta-badge.accent-violet { background: #312e81; color: #c7d2fe; border-color: #4338ca; }
.meta-badge.accent-green  { background: #14532d; color: #bbf7d0; border-color: #166534; }
.meta-badge.accent-amber  { background: #713f12; color: #fef08a; border-color: #854d0e; }
.meta-badge.accent-red    { background: #7f1d1d; color: #fca5a5; border-color: #991b1b; }

.section { background: #1e293b; border-radius: 12px;
           padding: 1.5rem; margin-bottom: 1.5rem; }
.section.with-left-bar-green  { border-left: 3px solid #10b981; }
.section.with-left-bar-amber  { border-left: 3px solid #fbbf24; }
.section.with-left-bar-red    { border-left: 3px solid #ef4444; }
.section.with-left-bar-violet { border-left: 3px solid #8b5cf6; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
@media (max-width: 768px) { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }

.stat-card { background: #1e293b; border-radius: 12px;
             padding: 1.25rem; text-align: center; }
.stat-num { font-size: 2.5rem; font-weight: 800; line-height: 1; }
.stat-label { font-size: 0.75rem; color: #94a3b8;
              text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }

.pipeline { display: flex; align-items: center; gap: 0;
            margin-bottom: 1.5rem; flex-wrap: wrap; }
.pipe-step { padding: 0.5rem 1rem; font-size: 0.72rem; font-weight: 600;
             text-transform: uppercase; letter-spacing: 0.03em; }
.pipe-step.done    { background: #166534; color: #bbf7d0; }
.pipe-step.active  { background: #854d0e; color: #fef08a; }
.pipe-step.pending { background: #334155; color: #64748b; }
.pipe-step:first-child { border-radius: 8px 0 0 8px; }
.pipe-step:last-child  { border-radius: 0 8px 8px 0; }

.contradiction { display: grid; grid-template-columns: 1fr auto 1fr;
                 gap: 1rem; align-items: center; margin-bottom: 1rem; }
.contradiction .pole { background: #0f172a; border-radius: 8px;
                       padding: 0.85rem; font-size: 0.9rem; }
.contradiction .pole .label { font-size: 0.7rem; font-weight: 700;
                              color: #94a3b8; text-transform: uppercase;
                              letter-spacing: 0.05em; margin-bottom: 0.35rem; }
.contradiction .vs { font-weight: 800; color: #8b5cf6;
                     font-size: 1.5rem; text-align: center; }
.constraint-list { font-size: 0.85rem; color: #cbd5e1; }
.constraint-list li { margin-left: 1.2rem; padding: 0.15rem 0; }

.matrix-card { background: #0f172a; border-radius: 8px;
               padding: 1rem; margin-bottom: 0.75rem; }
.matrix-card .id { font-weight: 700; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                   color: #c7d2fe; font-size: 0.95rem; margin-bottom: 0.25rem; }
.matrix-card .score { font-size: 0.78rem; color: #94a3b8; margin-bottom: 0.5rem; }
.matrix-card .rationale { font-size: 0.85rem; color: #cbd5e1; }

.principle-chip { display: inline-block; background: #312e81; color: #c7d2fe;
                  padding: 0.3rem 0.75rem; border-radius: 6px;
                  font-size: 0.78rem; margin: 0.2rem; font-weight: 600;
                  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }

.candidate-card { background: #0f172a; border-radius: 10px;
                  padding: 1.25rem; margin-bottom: 1rem;
                  border-left: 4px solid #475569; }
.candidate-card.sev-minor    { border-left-color: #166534; }
.candidate-card.sev-moderate { border-left-color: #854d0e; }
.candidate-card.sev-severe   { border-left-color: #9a3412; }
.candidate-card.sev-fatal    { border-left-color: #7f1d1d; }
.candidate-card.excluded { opacity: 0.55; }

.cand-head { display: flex; justify-content: space-between;
             align-items: flex-start; gap: 1rem; margin-bottom: 0.5rem;
             flex-wrap: wrap; }
.cand-head .title { font-size: 1.05rem; font-weight: 700; flex: 1; }
.cand-head .id { font-size: 0.7rem; color: #64748b;
                 font-family: ui-monospace, monospace; margin-right: 0.5rem; }
.sev-badge { padding: 0.2rem 0.6rem; border-radius: 9999px;
             font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.03em; white-space: nowrap; }
.sev-badge.minor    { background: #14532d; color: #bbf7d0; }
.sev-badge.moderate { background: #713f12; color: #fef08a; }
.sev-badge.severe   { background: #7c2d12; color: #fed7aa; }
.sev-badge.fatal    { background: #7f1d1d; color: #fca5a5; }
.sev-badge.excluded { background: #334155; color: #94a3b8; }

.cand-summary { font-size: 0.9rem; color: #cbd5e1; margin-bottom: 0.75rem; }
.cand-meta { font-size: 0.78rem; color: #94a3b8; margin-bottom: 0.75rem; }
.cand-meta .sep { color: #475569; margin: 0 0.5rem; }

details { margin-top: 0.5rem; }
details summary { cursor: pointer; padding: 0.4rem 0; font-weight: 600;
                  font-size: 0.85rem; color: #94a3b8; list-style: none;
                  display: flex; align-items: center; gap: 0.5rem; }
details summary::before { content: "▶"; font-size: 0.65rem;
                          transition: transform 0.2s; color: #64748b; }
details[open] summary::before { transform: rotate(90deg); }
details summary:hover { color: #e2e8f0; }
.detail-body { padding: 0.5rem 0 0.5rem 1rem;
               border-left: 2px solid #334155; margin-left: 0.3rem; }
.detail-body .field { font-size: 0.82rem; color: #cbd5e1; padding: 0.2rem 0; }
.detail-body .field-label { color: #94a3b8; font-weight: 600;
                            margin-right: 0.35rem; }
.detail-body ul { margin-left: 1.25rem; }
.detail-body li { font-size: 0.82rem; color: #cbd5e1; padding: 0.15rem 0; }
.detail-body .interp { font-size: 0.82rem; padding: 0.4rem 0;
                       border-bottom: 1px solid #1e293b; }
.detail-body .interp:last-child { border-bottom: none; }
.detail-body .interp .lineage { color: #8b5cf6; font-weight: 700;
                                font-family: ui-monospace, monospace; }
.detail-body .interp .pname { font-weight: 600; color: #e2e8f0; }

.verdict-pill { display: inline-block; padding: 0.25rem 0.75rem;
                border-radius: 6px; font-weight: 700; font-size: 0.78rem;
                text-transform: uppercase; letter-spacing: 0.03em; }
.verdict-pill.agree         { background: #14532d; color: #bbf7d0; }
.verdict-pill.disagree      { background: #7c2d12; color: #fed7aa; }
.verdict-pill.propose_third { background: #312e81; color: #c7d2fe; }

.trace-list { font-size: 0.78rem; color: #94a3b8;
              font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.trace-list li { padding: 0.15rem 0; }
.trace-list li.partial { color: #64748b; }

.footer { text-align: center; color: #475569; font-size: 0.75rem;
          margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #1e293b; }
"""


# --- Section renderers ---------------------------------------------------

def _render_header(run_id: str, problem: dict | None) -> str:
    if not problem:
        return (
            f"<h1>prizm run</h1>"
            f"<div class='subtitle'>Run: <code>{_esc(run_id)}</code></div>"
        )
    framing = problem.get("framing_confidence", "?")
    framing_color = FRAMING_COLORS.get(framing, "#64748b")
    contradiction_type = problem.get("contradiction_type", "?")
    domain = problem.get("domain_class", "?")
    badges = [
        f"<span class='meta-badge' "
        f"style='background:{framing_color}20;color:{framing_color};"
        f"border-color:{framing_color}'>framing: {_esc(framing)}</span>",
        f"<span class='meta-badge accent-violet'>{_esc(contradiction_type)}</span>",
        f"<span class='meta-badge'>{_esc(domain)}</span>",
    ]
    for s in (problem.get("domain_signals") or [])[:3]:
        badges.append(f"<span class='meta-badge'>{_esc(s)}</span>")
    for s in (problem.get("exotic_signals") or [])[:3]:
        badges.append(f"<span class='meta-badge accent-amber'>{_esc(s)}</span>")
    return (
        f"<div style='margin-bottom:2rem;'>"
        f"<h1>prizm</h1>"
        f"<div class='subtitle'>Run <code>{_esc(run_id)}</code></div>"
        f"<div class='meta-row'>{''.join(badges)}</div>"
        f"</div>"
    )


def _render_pipeline(state: dict | None) -> str:
    """Render the 9-stage pipeline; mark every stage 'done' on a finished run.

    If state.json shows current_stage != done, mark the current stage
    'active' and following stages 'pending'.
    """
    stages = [
        ("framer", "Frame"),
        ("select_matrix", "Select"),
        ("mapping_phase1", "Map"),
        ("compare_mappings", "Critic"),
        ("lookup", "Lookup"),
        ("interpret", "Interpret"),
        ("synthesize", "Synthesize"),
        ("critique", "Critique"),
        ("assemble", "Assemble"),
    ]
    completed = set((state or {}).get("completed_stages", []))
    current = (state or {}).get("current_stage", "done")
    cells = []
    for sid, label in stages:
        if sid in completed or current == "done":
            cls = "done"
        elif current == sid:
            cls = "active"
        else:
            cls = "pending"
        cells.append(f"<div class='pipe-step {cls}'>{_esc(label)}</div>")
    # final cell mirrors completion state
    final_cls = "done" if current == "done" else "active"
    cells.append(f"<div class='pipe-step {final_cls}'>Complete</div>")
    return f"<div class='pipeline'>{''.join(cells)}</div>"


def _render_stats(
    selection: dict | None,
    principles_files: list[dict],
    solutions: dict | None,
    critique: dict | None,
    excluded: set[str],
) -> str:
    n_matrices = len((selection or {}).get("selected_matrices", []) or [])
    n_principles = sum(len(p.get("principles", []) or []) for p in principles_files)
    cands = (solutions or {}).get("candidates", []) or []
    n_candidates = len(cands)
    n_excluded = 0
    for idx, c in enumerate(cands):
        sid = f"s{idx + 1}"
        if c.get("name") in excluded or sid in excluded:
            n_excluded += 1
    crits = (critique or {}).get("per_solution_critiques", []) or []
    sev_counts = {"minor": 0, "moderate": 0, "severe": 0, "fatal": 0}
    for c in crits:
        s = c.get("severity")
        if s in sev_counts:
            sev_counts[s] += 1
    cells = [
        ("#8b5cf6", n_matrices, "Matrices"),
        ("#c7d2fe", n_principles, "Principles"),
        ("#10b981", n_candidates - n_excluded, "Candidates Rendered"),
        ("#ef4444", sev_counts["fatal"], "Fatal Severity"),
    ]
    cell_html = "".join(
        f"<div class='stat-card'>"
        f"<div class='stat-num' style='color:{color}'>{num}</div>"
        f"<div class='stat-label'>{_esc(label)}</div>"
        f"</div>"
        for color, num, label in cells
    )
    # Secondary severity row
    sev_row = (
        f"<div class='grid-4' style='margin-bottom:1.5rem;'>"
        f"<div class='stat-card'><div class='stat-num' style='color:#bbf7d0;font-size:1.5rem;'>"
        f"{sev_counts['minor']}</div><div class='stat-label'>Minor</div></div>"
        f"<div class='stat-card'><div class='stat-num' style='color:#fef08a;font-size:1.5rem;'>"
        f"{sev_counts['moderate']}</div><div class='stat-label'>Moderate</div></div>"
        f"<div class='stat-card'><div class='stat-num' style='color:#fed7aa;font-size:1.5rem;'>"
        f"{sev_counts['severe']}</div><div class='stat-label'>Severe</div></div>"
        f"<div class='stat-card'><div class='stat-num' style='color:#fca5a5;font-size:1.5rem;'>"
        f"{sev_counts['fatal']}</div><div class='stat-label'>Fatal</div></div>"
        f"</div>"
    )
    return (
        f"<div class='grid-4' style='margin-bottom:1.5rem;'>{cell_html}</div>"
        + sev_row
    )


def _render_contradiction(problem: dict | None) -> str:
    if not problem:
        return ""
    improving = _esc(problem.get("improving_concept", "?"))
    worsening = _esc(problem.get("worsening_concept", "?"))
    constraints = problem.get("constraints", []) or []
    rationale = problem.get("rationale", "")
    parts = [
        "<div class='section with-left-bar-violet'>",
        "<h2>Contradiction</h2>",
        "<div class='contradiction'>",
        f"<div class='pole'><div class='label'>Improving</div>{improving}</div>",
        "<div class='vs'>⇄</div>",
        f"<div class='pole'><div class='label'>Worsening</div>{worsening}</div>",
        "</div>",
    ]
    if constraints:
        parts.append(
            "<details><summary>Constraints "
            f"({len(constraints)})</summary><div class='detail-body'>"
            "<ul class='constraint-list'>"
            + "".join(f"<li>{_esc(c)}</li>" for c in constraints)
            + "</ul></div></details>"
        )
    if rationale:
        parts.append(
            "<details><summary>Framer rationale</summary>"
            f"<div class='detail-body'><div class='field'>{_esc(rationale)}</div></div>"
            "</details>"
        )
    parts.append("</div>")
    return "".join(parts)


def _render_selection(selection: dict | None) -> str:
    if not selection:
        return ""
    selected = selection.get("selected_matrices", []) or []
    rejected = selection.get("rejected_matrices", []) or []
    strategy = selection.get("run_strategy", "?")
    stage_e = selection.get("stage_e_invoked", False)
    parts = [
        "<div class='section'>",
        "<h2>Matrix Selection</h2>",
        "<div class='meta-row'>",
        f"<span class='meta-badge accent-violet'>strategy: {_esc(strategy)}</span>",
        f"<span class='meta-badge {'accent-amber' if stage_e else ''}'>"
        f"Stage E: {'invoked' if stage_e else 'not invoked'}</span>",
        f"<span class='meta-badge'>weights {_esc(selection.get('weights_version', '?'))}</span>",
        "</div>",
    ]
    for m in selected:
        parts.append(
            "<div class='matrix-card'>"
            f"<div class='id'>{_esc(m.get('matrix_id', '?'))}</div>"
            f"<div class='score'>score "
            f"{_esc(m.get('score', '?'))} · confidence "
            f"{_esc(m.get('selection_confidence', '?'))}</div>"
            f"<div class='rationale'>{_esc(m.get('rationale', ''))}</div>"
            "</div>"
        )
    if rejected:
        parts.append(
            "<details><summary>Rejected matrices "
            f"({len(rejected)})</summary><div class='detail-body'>"
            + "".join(
                "<div class='field'>"
                f"<span class='field-label'>{_esc(r.get('matrix_id', '?'))}:</span>"
                f"{_esc(r.get('reason', ''))} "
                f"<em>(stage {_esc(r.get('stage', '?'))})</em>"
                "</div>"
                for r in rejected
            )
            + "</div></details>"
        )
    parts.append("</div>")
    return "".join(parts)


def _render_mapping_and_critic(run_id: str) -> str:
    mappings = _glob_load(run_id, "03_mapping_*.json")
    # Filter out 03b_ and 03c_ which globbed because they share prefix.
    mappings = [m for m in mappings
                if not m["__path"].startswith(("03b_", "03c_"))]
    critiques = _glob_load(run_id, "03b_mapping_critique_*.json")
    independents = _glob_load(run_id, "03c_independent_mapping_*.json")
    if not mappings:
        return ""
    crit_by_matrix = {c.get("matrix_id"): c for c in critiques}
    indep_by_matrix = {c.get("matrix_id"): c for c in independents}
    parts = [
        "<div class='section'>",
        "<h2>Mapping &amp; Two-Phase Critic</h2>",
    ]
    for m in mappings:
        mid = m.get("matrix_id", "?")
        imp = m.get("improving_param_id", "?")
        wor = m.get("worsening_param_id", "?")
        crit = crit_by_matrix.get(mid)
        indep = indep_by_matrix.get(mid)
        # Resolved cell: the verdict (if disagreed) overrides the mapper's.
        resolved_imp, resolved_wor = imp, wor
        verdict = None
        if crit:
            verdict = crit.get("verdict")
            if verdict in {"disagree", "propose_third"}:
                chosen = crit.get("chosen_mapping") or {}
                resolved_imp = chosen.get("improving_param_id", imp)
                resolved_wor = chosen.get("worsening_param_id", wor)
        verdict_str = verdict or ("agree" if indep else "n/a")
        verdict_cls = verdict_str if verdict_str in VERDICT_COLORS else "agree"
        parts.append(
            "<div class='matrix-card'>"
            f"<div class='id'>{_esc(mid)}</div>"
            "<div class='score'>"
            f"resolved cell: <strong style='color:#c7d2fe'>"
            f"{_esc(resolved_imp)} × {_esc(resolved_wor)}</strong>"
            "</div>"
            "<div style='margin-top:0.5rem;'>"
            f"<span class='verdict-pill {verdict_cls}'>"
            f"phase-2 verdict: {_esc(verdict_str)}</span>"
            "</div>"
        )
        if indep or crit:
            parts.append(
                "<details><summary>Phase 1 + Phase 2 details</summary>"
                "<div class='detail-body'>"
            )
            parts.append(
                f"<div class='field'><span class='field-label'>Mapper:</span>"
                f"{_esc(imp)} × {_esc(wor)} "
                f"(confidence {_esc(m.get('mapping_confidence', '?'))})</div>"
            )
            if indep:
                parts.append(
                    "<div class='field'>"
                    f"<span class='field-label'>Blind critic:</span>"
                    f"{_esc(indep.get('improving_param_id', '?'))} × "
                    f"{_esc(indep.get('worsening_param_id', '?'))} "
                    f"(confidence {_esc(indep.get('confidence', '?'))})</div>"
                )
            if crit:
                parts.append(
                    "<div class='field'>"
                    f"<span class='field-label'>Verdict reasoning:</span>"
                    f"{_esc(crit.get('reasoning', ''))[:600]}</div>"
                )
            parts.append("</div></details>")
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)


def _render_principles(run_id: str) -> str:
    files = _glob_load(run_id, "04_principles_*.json")
    if not files:
        return ""
    parts = [
        "<div class='section'>",
        "<h2>Inventive Principles Surfaced</h2>",
    ]
    for f in files:
        mid = f.get("matrix_id", "?")
        pids = f.get("principles", []) or []
        parts.append(
            f"<h3 style='margin-top:0.5rem;font-size:0.9rem;color:#94a3b8;'>"
            f"<code>{_esc(mid)}</code></h3>"
        )
        if not pids:
            parts.append(
                "<div class='field'>(no principles — empty cell)</div>"
            )
        else:
            parts.append(
                "<div>"
                + "".join(
                    f"<span class='principle-chip'>P{_esc(p)}</span>" for p in pids
                )
                + "</div>"
            )
    parts.append("</div>")
    return "".join(parts)


def _render_candidates(
    solutions: dict | None,
    critique: dict | None,
    interpretations: dict | None,
    excluded: set[str],
    override_logged: bool,
) -> str:
    if not solutions:
        return ""
    cands = solutions.get("candidates", []) or []
    crits_by_name: dict[str, dict] = {}
    if critique:
        for c in critique.get("per_solution_critiques", []) or []:
            crits_by_name[c.get("candidate_name", "")] = c
    interp_by_ref: dict[tuple, dict] = {}
    if interpretations:
        for e in interpretations.get("interpretations", []) or []:
            key = (e.get("matrix_id", ""), str(e.get("principle_id", "")))
            interp_by_ref[key] = e
    parts = [
        "<div class='section'>",
        f"<h2>Candidate Solutions ({len(cands)})</h2>",
    ]
    for idx, cand in enumerate(cands):
        sid = f"s{idx + 1}"
        is_excluded = cand.get("name") in excluded or sid in excluded
        crit = crits_by_name.get(cand.get("name", ""))
        severity = (crit or {}).get("severity", "minor")
        sev_cls = severity if severity in SEVERITY_COLORS else "minor"
        card_classes = ["candidate-card", f"sev-{sev_cls}"]
        if is_excluded:
            card_classes.append("excluded")
        badge_cls = "excluded" if is_excluded else sev_cls
        badge_label = "EXCLUDED" if is_excluded else severity.upper()
        parts.append(
            f"<div class='{' '.join(card_classes)}'>"
            "<div class='cand-head'>"
            f"<div><span class='id'>{sid}</span><span class='title'>"
            f"{_esc(cand.get('name', '?'))}</span></div>"
            f"<span class='sev-badge {badge_cls}'>{_esc(badge_label)}</span>"
            "</div>"
        )
        parts.append(
            f"<div class='cand-summary'>{_esc(cand.get('summary', ''))}</div>"
        )
        parts.append(
            "<div class='cand-meta'>"
            f"novelty <strong>{_esc(cand.get('novelty_estimate', '?'))}</strong>"
            "<span class='sep'>·</span>"
            f"effort <strong>{_esc(cand.get('effort_estimate', '?'))}</strong>"
            "<span class='sep'>·</span>"
            f"principles "
            + ", ".join(
                f"<code>{_esc(p)}</code>"
                for p in cand.get("principles_applied", []) or []
            )
            + "</div>"
        )
        if override_logged and not is_excluded and severity == "fatal":
            parts.append(
                "<div class='field' style='background:#7f1d1d;color:#fca5a5;"
                "border-radius:6px;padding:0.5rem 0.75rem;font-size:0.78rem;'>"
                "Accepted with explicit user override despite fatal severity."
                "</div>"
            )
        # Implementation sketch — collapsed by default.
        sketch = cand.get("implementation_sketch", "")
        if sketch:
            parts.append(
                "<details><summary>Implementation sketch</summary>"
                "<div class='detail-body'><div class='field' "
                "style='white-space:pre-wrap;'>"
                f"{_esc(sketch)}</div></div></details>"
            )
        # Interpretation contributions.
        refs = cand.get("interpretation_refs", []) or []
        if refs:
            parts.append(
                "<details><summary>"
                f"Interpretations contributing ({len(refs)})</summary>"
                "<div class='detail-body'>"
            )
            for ref in refs:
                key = (ref.get("matrix_id", ""), str(ref.get("principle_id", "")))
                e = interp_by_ref.get(key)
                if e:
                    parts.append(
                        "<div class='interp'>"
                        f"<span class='lineage'>{_esc(e.get('interpretation_lineage', '?'))}</span>"
                        " on "
                        f"<span class='pname'>{_esc(e.get('principle_name', '?'))}</span>"
                        f" <code style='color:#64748b;'>({_esc(key[0])})</code>"
                        f"<div style='margin-top:0.25rem;color:#cbd5e1;'>"
                        f"{_esc(e.get('concrete_suggestion', ''))}</div>"
                        "</div>"
                    )
                else:
                    parts.append(
                        f"<div class='interp' style='color:#64748b;'>"
                        f"(missing interpretation for {_esc(key)})</div>"
                    )
            parts.append("</div></details>")
        # Critique details.
        if crit:
            parts.append(
                "<details><summary>Critique</summary>"
                "<div class='detail-body'>"
                f"<div class='field'><span class='field-label'>Severity:</span>"
                f"{_esc(crit.get('severity', '?'))}</div>"
                f"<div class='field'><span class='field-label'>Recommendation:</span>"
                f"{_esc(crit.get('recommendation', ''))}</div>"
            )
            sec = crit.get("secondary_contradictions", []) or []
            if sec:
                parts.append(
                    "<div class='field'><span class='field-label'>"
                    "Secondary contradictions:</span></div><ul>"
                )
                for s in sec:
                    parts.append(
                        "<li>"
                        f"{_esc(s.get('improving', '?'))} ⇄ "
                        f"{_esc(s.get('worsening', '?'))} "
                        f"<em>({_esc(s.get('severity', '?'))})</em>"
                        "</li>"
                    )
                parts.append("</ul>")
            risks = crit.get("risks", []) or []
            if risks:
                parts.append(
                    "<div class='field'><span class='field-label'>Risks:</span></div>"
                    "<ul>"
                    + "".join(f"<li>{_esc(r)}</li>" for r in risks)
                    + "</ul>"
                )
            parts.append("</div></details>")
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)


def _render_footer(run_id: str) -> str:
    rd = _common.run_dir(run_id, create=False)
    top = sorted(p.name for p in rd.glob("0*.json"))
    partial_dir = rd / "partial"
    partial = sorted(p.name for p in partial_dir.glob("*.json")) \
        if partial_dir.exists() else []
    parts = [
        "<div class='section'>",
        "<h2>Trace</h2>",
        f"<div class='field'><span class='field-label'>Run dir:</span>"
        f"<code>{_esc(rd)}</code></div>",
        f"<div class='field'><span class='field-label'>Artifacts:</span>"
        f"{len(top) + len(partial)} "
        f"(top-level {len(top)}, partial/ {len(partial)})</div>",
        "<details><summary>Artifact list</summary>"
        "<div class='detail-body'><ul class='trace-list'>",
    ]
    for a in top:
        parts.append(f"<li>{_esc(a)}</li>")
    for a in partial:
        parts.append(f"<li class='partial'>partial/{_esc(a)}</li>")
    parts.append("</ul></div></details></div>")
    parts.append(
        "<div class='footer'>Generated by prizm "
        "generate_digest.py</div>"
    )
    return "".join(parts)


# --- Top-level assemble --------------------------------------------------

def render_digest(run_id: str, excluded: set[str], override_logged: bool) -> str:
    problem = _safe_load(run_id, "01_problem.json")
    selection = _safe_load(run_id, "02_selection.json")
    interpretations = _safe_load(run_id, "05_interpretations.json")
    solutions = _safe_load(run_id, "06_solutions.json")
    critique = _safe_load(run_id, "07_critique.json")
    state = _safe_load(run_id, "state.json")
    principles_files = _glob_load(run_id, "04_principles_*.json")

    title = "prizm · digest"
    if problem:
        improving = problem.get("improving_concept", "")[:80]
        if improving:
            title = f"prizm · {improving}"

    body = (
        _render_header(run_id, problem)
        + _render_pipeline(state)
        + _render_stats(selection, principles_files, solutions,
                        critique, excluded)
        + _render_contradiction(problem)
        + _render_selection(selection)
        + _render_mapping_and_critic(run_id)
        + _render_principles(run_id)
        + _render_candidates(solutions, critique, interpretations,
                             excluded, override_logged)
        + _render_footer(run_id)
    )

    return (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "<meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>\n"
        f"<title>{_esc(title)}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate_digest.py",
        description="Render digest.html for a prizm run "
                    "(visual companion to final-report.md).",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--exclude", action="append", default=None,
        help="Candidate name OR solution id (s1, s2, ...) to drop.",
    )
    parser.add_argument(
        "--override_logged", action="store_true",
        help="Stamp the accept_with_override note on the fatal candidate.",
    )
    args = parser.parse_args(argv)

    excluded = set(args.exclude or [])
    try:
        text = render_digest(args.run_id, excluded, args.override_logged)
    except Exception as e:
        print(f"generate_digest: failed: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 2
    rd = _common.run_dir(args.run_id)
    out = rd / "digest.html"
    # digest.html is not a schema-validated artifact; pass validate=False
    # to skip the gate atomic_write applies for known artifact filenames.
    _common.atomic_write(out, text, validate=False)
    print(f"generate_digest: wrote {out} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"generate_digest: internal error: {type(e).__name__}: {e}",
              file=sys.stderr)
        sys.exit(2)
