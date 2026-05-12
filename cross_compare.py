#!/usr/bin/env python3
"""Cross-compare all 39x39 TRIZ contradiction matrix JSON files.

Loads altshuller_39x39.json, heinrich_39x39.json, matriz_org_39x39.json,
and altshuller_russian_original.json, then compares every cell and reports
discrepancies between sources.
"""

import json
import os
import sys
from collections import defaultdict


MATRICES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matrices')

FILES = {
    'altshuller': os.path.join(MATRICES_DIR, 'altshuller_39x39.json'),
    'heinrich': os.path.join(MATRICES_DIR, 'heinrich_39x39.json'),
    'matriz_org': os.path.join(MATRICES_DIR, 'matriz_org_39x39.json'),
    'russian_orig': os.path.join(MATRICES_DIR, 'altshuller_russian_original.json'),
}


def load_matrix(filepath):
    """Load a JSON matrix file and return (parameters, matrix_data, principles)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    params = data.get('parameters', {})
    principles = data.get('principles', {})
    # Find the matrix key (could be 'matrix', 'matrix_technology', etc.)
    matrix_keys = [k for k in data if k.startswith('matrix')]
    matrix = {}
    for mk in matrix_keys:
        if mk == 'matrix':
            matrix = data[mk]
            break
    if not matrix and matrix_keys:
        matrix = data[matrix_keys[0]]
    return params, matrix, principles


def sorted_cell(cell_list):
    """Return a sorted tuple of principle numbers for comparison."""
    if cell_list is None:
        return None
    return tuple(sorted(cell_list))


def compare_cells(matrices_data):
    """Compare every cell across all matrices. Returns discrepancies."""
    discrepancies = []
    all_cells = set()

    # Collect all (improving, worsening) pairs across all matrices
    for name, (params, matrix, principles) in matrices_data.items():
        for imp in matrix:
            for wor in matrix[imp]:
                all_cells.add((imp, wor))

    for imp, wor in sorted(all_cells, key=lambda x: (int(x[0]), int(x[1]))):
        cell_values = {}
        for name, (params, matrix, principles) in matrices_data.items():
            val = matrix.get(imp, {}).get(wor, None)
            if val is not None:
                cell_values[name] = sorted_cell(val)
            else:
                cell_values[name] = None

        # Check for discrepancies among sources that have data for this cell
        present = {k: v for k, v in cell_values.items() if v is not None}
        if len(present) >= 2:
            unique_values = set(present.values())
            if len(unique_values) > 1:
                discrepancies.append({
                    'cell': (imp, wor),
                    'values': {k: list(v) if v else None for k, v in cell_values.items()},
                    'present': {k: list(v) for k, v in present.items()},
                })

    return discrepancies


def compare_parameters(matrices_data):
    """Compare parameter names across matrices."""
    diffs = []
    all_param_ids = set()
    for name, (params, matrix, principles) in matrices_data.items():
        all_param_ids.update(params.keys())

    for pid in sorted(all_param_ids, key=lambda x: int(x)):
        names = {}
        for source_name, (params, matrix, principles) in matrices_data.items():
            if pid in params:
                names[source_name] = params[pid].get('name', '(no name)')
        unique_names = set(names.values())
        if len(unique_names) > 1:
            diffs.append({'param_id': pid, 'names': names})

    return diffs


def compare_principles(matrices_data):
    """Compare principle names across matrices."""
    diffs = []
    all_principle_ids = set()
    for name, (params, matrix, principles) in matrices_data.items():
        all_principle_ids.update(principles.keys())

    for pid in sorted(all_principle_ids, key=lambda x: int(x)):
        names = {}
        for source_name, (params, matrix, principles) in matrices_data.items():
            if pid in principles:
                names[source_name] = principles[pid].get('name', '(no name)')
        unique_names = set(names.values())
        if len(unique_names) > 1:
            diffs.append({'principle_id': pid, 'names': names})

    return diffs


def cell_coverage_analysis(matrices_data):
    """Analyze which cells are covered by which sources."""
    coverage = defaultdict(set)
    for name, (params, matrix, principles) in matrices_data.items():
        for imp in matrix:
            for wor in matrix[imp]:
                coverage[(imp, wor)].add(name)

    # Count by coverage level
    by_count = defaultdict(int)
    for cell, sources in coverage.items():
        by_count[len(sources)] += 1

    return coverage, by_count


def consensus_analysis(matrices_data):
    """Find cells where all sources that have data agree."""
    all_cells = set()
    for name, (params, matrix, principles) in matrices_data.items():
        for imp in matrix:
            for wor in matrix[imp]:
                all_cells.add((imp, wor))

    consensus_cells = []
    disagreement_cells = []

    for imp, wor in sorted(all_cells, key=lambda x: (int(x[0]), int(x[1]))):
        present = {}
        for name, (params, matrix, principles) in matrices_data.items():
            val = matrix.get(imp, {}).get(wor, None)
            if val is not None:
                present[name] = sorted_cell(val)

        if len(present) >= 2:
            if len(set(present.values())) == 1:
                consensus_cells.append((imp, wor))
            else:
                disagreement_cells.append((imp, wor))

    return consensus_cells, disagreement_cells


def principle_frequency_analysis(matrices_data):
    """Analyze principle frequency across all matrices combined."""
    freq = defaultdict(int)
    for name, (params, matrix, principles) in matrices_data.items():
        for imp in matrix:
            for wor in matrix[imp]:
                for p in matrix[imp][wor]:
                    freq[p] += 1
    return dict(sorted(freq.items(), key=lambda x: -x[1]))


def main():
    print("=" * 70)
    print("TRIZ 39x39 Matrix Cross-Comparison Report")
    print("=" * 70)

    # Load all matrices
    matrices_data = {}
    for name, filepath in FILES.items():
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping")
            continue
        params, matrix, principles = load_matrix(filepath)
        matrices_data[name] = (params, matrix, principles)
        cell_count = sum(len(row) for row in matrix.values())
        print(f"  Loaded {name}: {len(params)} params, {cell_count} cells")

    print()

    # 1. Parameter name comparison
    print("-" * 70)
    print("1. PARAMETER NAME DIFFERENCES")
    print("-" * 70)
    param_diffs = compare_parameters(matrices_data)
    if param_diffs:
        for d in param_diffs:
            print(f"\n  Parameter {d['param_id']}:")
            for source, name in d['names'].items():
                print(f"    {source}: \"{name}\"")
    else:
        print("  No parameter name differences found across all sources.")

    print()

    # 2. Principle name comparison
    print("-" * 70)
    print("2. PRINCIPLE NAME DIFFERENCES")
    print("-" * 70)
    principle_diffs = compare_principles(matrices_data)
    if principle_diffs:
        for d in principle_diffs:
            print(f"\n  Principle {d['principle_id']}:")
            for source, name in d['names'].items():
                print(f"    {source}: \"{name}\"")
    else:
        print("  No principle name differences found across all sources.")

    print()

    # 3. Cell-by-cell comparison
    print("-" * 70)
    print("3. CELL DISCREPANCIES")
    print("-" * 70)
    discrepancies = compare_cells(matrices_data)
    if discrepancies:
        print(f"\n  Found {len(discrepancies)} cells where sources disagree:\n")
        for d in discrepancies:
            imp, wor = d['cell']
            print(f"  Cell ({imp},{wor}):")
            for source, vals in d['present'].items():
                print(f"    {source}: {vals}")
            print()
    else:
        print("  No cell discrepancies found - all sources agree on shared cells.")

    print()

    # 4. Coverage analysis
    print("-" * 70)
    print("4. CELL COVERAGE ANALYSIS")
    print("-" * 70)
    coverage, by_count = cell_coverage_analysis(matrices_data)
    print(f"\n  Total unique cells across all sources: {len(coverage)}")
    for count in sorted(by_count.keys(), reverse=True):
        print(f"    Cells present in {count} source(s): {by_count[count]}")

    print()

    # 5. Consensus analysis
    print("-" * 70)
    print("5. CONSENSUS ANALYSIS")
    print("-" * 70)
    consensus, disagreement = consensus_analysis(matrices_data)
    multi_source = len(consensus) + len(disagreement)
    print(f"\n  Cells present in 2+ sources: {multi_source}")
    print(f"  Cells where all sources agree: {len(consensus)}")
    print(f"  Cells where sources disagree: {len(disagreement)}")
    if multi_source > 0:
        print(f"  Agreement rate: {len(consensus)/multi_source*100:.1f}%")

    if disagreement:
        print(f"\n  Disagreement details:")
        for imp, wor in disagreement:
            vals = {}
            for name, (params, matrix, principles) in matrices_data.items():
                v = matrix.get(imp, {}).get(wor, None)
                if v is not None:
                    vals[name] = sorted(v)
            print(f"    ({imp},{wor}): {vals}")

    print()

    # 6. Principle frequency
    print("-" * 70)
    print("6. PRINCIPLE FREQUENCY (across all 39x39 matrices combined)")
    print("-" * 70)
    freq = principle_frequency_analysis(matrices_data)
    for pid, count in list(freq.items())[:10]:
        pname = matrices_data['altshuller'][2].get(str(pid), {}).get('name', '?')
        print(f"  P{pid} ({pname}): {count} appearances")
    print(f"  ... ({len(freq)} principles total)")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Files compared: {len(matrices_data)}")
    print(f"  Parameter name differences: {len(param_diffs)}")
    print(f"  Principle name differences: {len(principle_diffs)}")
    print(f"  Cell discrepancies: {len(discrepancies)}")
    if multi_source > 0:
        print(f"  Overall agreement rate: {len(consensus)/multi_source*100:.1f}%")

    # Return results for use in reports
    return {
        'param_diffs': param_diffs,
        'principle_diffs': principle_diffs,
        'discrepancies': discrepancies,
        'coverage': coverage,
        'by_count': by_count,
        'consensus_count': len(consensus),
        'disagreement_count': len(disagreement),
        'multi_source_count': multi_source,
        'freq': freq,
    }


if __name__ == '__main__':
    main()
