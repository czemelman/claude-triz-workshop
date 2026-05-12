#!/usr/bin/env python3
"""Validates a TRIZ matrix JSON file against the schema and internal-consistency rules.

Two modes:
  - default (legacy): the original v1.0 checks (kept for backward-compat).
  - --strict: v6/v1.1 contracts including canonical_id, interpretation_lineage,
    structured dimensions, language tag, status enum, registry consistency,
    skip_in_favor_of DSL parsing, redirect cycle detection, and use-case schema.

Usage:
  validate_matrix.py [--strict] [files...]
  validate_matrix.py --strict        # validates the whole live corpus + registry + use_cases
"""

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Any

ROOT          = os.path.dirname(os.path.abspath(__file__))
MATRICES_DIR  = os.path.join(ROOT, 'matrices')
USECASES_DIR  = os.path.join(ROOT, 'use_cases')
REGISTRY_PATH = os.path.join(ROOT, 'registry.json')
VOCAB_PATH    = os.path.join(ROOT, 'selector_tags_vocabulary.json')

# ---------------------------------------------------------------------------
# Legacy validation (original behavior, lightly fixed for structured dims).
# ---------------------------------------------------------------------------

def validate_matrix(filepath):
    errors, warnings = [], []
    data = json.load(open(filepath, 'r', encoding='utf-8'))

    for key in ['meta', 'parameters', 'principles']:
        if key not in data:
            errors.append(f"Missing required top-level key: {key}")

    matrix_keys = [k for k in data if k.startswith('matrix') and isinstance(data[k], dict)]
    if not matrix_keys:
        errors.append("No matrix key found (expected 'matrix' or 'matrix_*')")
    if errors:
        return errors, warnings, {}

    meta = data.get('meta', {})
    for f in ['name', 'version', 'author', 'year', 'dimensions', 'source_url', 'license', 'notes']:
        if f not in meta:
            warnings.append(f"meta.{f} is missing")

    parameters = data['parameters']
    principles = data['principles']
    param_ids = set(parameters.keys())
    principle_ids = set(principles.keys())
    diagonal_allowed = meta.get('diagonal_cells') == 'included'

    stats = {}
    for matrix_key in matrix_keys:
        matrix = data[matrix_key]
        referenced_principles, referenced_params = set(), set()
        total_cells, cell_sizes = 0, []
        principle_counts, seen_cells = {}, set()

        for improving_id, row in matrix.items():
            if not isinstance(row, dict):
                continue
            referenced_params.add(improving_id)
            if improving_id not in param_ids:
                errors.append(f"[{matrix_key}] Improving param '{improving_id}' not in parameters")
            for worsening_id, principles_list in row.items():
                referenced_params.add(worsening_id)
                if worsening_id not in param_ids:
                    errors.append(f"[{matrix_key}] Worsening param '{worsening_id}' not in parameters")
                if improving_id == worsening_id:
                    if diagonal_allowed:
                        warnings.append(f"[{matrix_key}] Diagonal entry: '{improving_id}' (allowed: diagonal_cells=included)")
                    else:
                        errors.append(f"[{matrix_key}] Diagonal entry: '{improving_id}' maps to itself")
                cell_key = (improving_id, worsening_id)
                if cell_key in seen_cells:
                    errors.append(f"[{matrix_key}] Duplicate cell: ({improving_id}, {worsening_id})")
                seen_cells.add(cell_key)
                if not isinstance(principles_list, list):
                    errors.append(f"[{matrix_key}] Cell ({improving_id}, {worsening_id}) is not a list")
                    continue
                if len(principles_list) == 0:
                    errors.append(f"[{matrix_key}] Cell ({improving_id}, {worsening_id}) is empty (should be omitted)")
                    continue
                total_cells += 1
                cell_sizes.append(len(principles_list))
                for pid in principles_list:
                    if not isinstance(pid, int):
                        errors.append(f"[{matrix_key}] Cell ({improving_id}, {worsening_id}) non-integer principle: {pid}")
                    else:
                        pid_str = str(pid)
                        referenced_principles.add(pid_str)
                        principle_counts[pid_str] = principle_counts.get(pid_str, 0) + 1

        for pid in referenced_principles:
            if pid not in principle_ids:
                errors.append(f"[{matrix_key}] Principle '{pid}' referenced but not defined")
        unreferenced = principle_ids - referenced_principles
        if unreferenced and matrix_key == 'matrix':
            warnings.append(f"[{matrix_key}] Principles defined but never referenced: "
                            f"{sorted(unreferenced, key=lambda x: int(x) if x.isdigit() else 999)}")

        n_params = len(param_ids)
        total_possible = n_params * (n_params - 1) if not diagonal_allowed else n_params * n_params
        sparsity = (1 - total_cells / total_possible) * 100 if total_possible > 0 else 0
        stats[matrix_key] = {
            'parameters': n_params,
            'principles_defined': len(principle_ids),
            'principles_referenced': len(referenced_principles),
            'total_populated_cells': total_cells,
            'total_possible_cells': total_possible,
            'sparsity_pct': round(sparsity, 2),
            'avg_principles_per_cell': round(sum(cell_sizes)/len(cell_sizes), 2) if cell_sizes else 0,
            'max_principles_in_cell': max(cell_sizes) if cell_sizes else 0,
            'min_principles_in_cell': min(cell_sizes) if cell_sizes else 0,
        }
    return errors, warnings, stats

# ---------------------------------------------------------------------------
# v6 / v1.1 strict validation.
# ---------------------------------------------------------------------------

CANONICAL_ID_RE       = re.compile(r'^P_[A-Z][A-Z_]*$')
INTERP_LINEAGE_VALUES = {'altshuller-40', 'biotriz-40', 'drug-safety-reframed', 'triz-ai-extended'}
STATUS_VALUES         = {'canonical', 'variant', 'derived', 'domain', 'experimental', 'shell', 'identical-duplicate'}
PARAM_ID_STYLES       = {'numeric', 'prefixed', 'alphanumeric'}
DIAGONAL_VALUES       = {'included', 'excluded'}
DSL_PREDICATES        = {'exotic_signal', 'domain_signal', 'contradiction_type_is',
                         'domain_class_is', 'language_is', 'populated_cells_at_least'}
DSL_COMBINATORS       = {'any_of', 'all_of', 'not'}

def _hash_cells(matrix: dict) -> str:
    """Deterministic hash of cell contents for lineage.identical_to verification."""
    canonical = json.dumps(matrix, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()

def _validate_dsl(node: Any, path: str, errors: list) -> None:
    """Recursively validate a skip_in_favor_of[].if DSL node. Closed predicate/combinator set."""
    if not isinstance(node, dict):
        errors.append(f"{path}: must be an object")
        return
    if len(node) != 1:
        errors.append(f"{path}: must have exactly one key (predicate or combinator), got {list(node.keys())}")
        return
    key, val = next(iter(node.items()))
    if key in DSL_PREDICATES:
        if not isinstance(val, (str, int)):
            errors.append(f"{path}.{key}: predicate value must be string or int")
    elif key in DSL_COMBINATORS:
        if key == 'not':
            _validate_dsl(val, f'{path}.not', errors)
        else:  # any_of, all_of
            if not isinstance(val, list) or not val:
                errors.append(f"{path}.{key}: must be a non-empty array")
            else:
                for i, child in enumerate(val):
                    _validate_dsl(child, f'{path}.{key}[{i}]', errors)
    else:
        errors.append(f"{path}: unknown predicate/combinator {key!r}; allowed: "
                      f"{sorted(DSL_PREDICATES | DSL_COMBINATORS)}")

def validate_matrix_strict(filepath: str, vocab: dict) -> tuple[list, list]:
    """Returns (errors, warnings) for v6 contract violations on a single matrix file."""
    errors, warnings = [], []
    data = json.load(open(filepath, 'r', encoding='utf-8'))
    meta = data.get('meta', {})
    fname_stem = os.path.splitext(os.path.basename(filepath))[0]

    # meta.id matches filename stem
    if meta.get('id') != fname_stem:
        errors.append(f"meta.id={meta.get('id')!r} does not match filename stem {fname_stem!r}")

    # meta.status in closed set
    if meta.get('status') not in STATUS_VALUES:
        errors.append(f"meta.status={meta.get('status')!r} not in {sorted(STATUS_VALUES)}")

    # meta.dimensions is a structured object
    dims = meta.get('dimensions')
    if not isinstance(dims, dict):
        errors.append(f"meta.dimensions must be an object {{rows, cols, populated_cells}}, got {type(dims).__name__}")
    else:
        for k in ('rows', 'cols', 'populated_cells'):
            if not isinstance(dims.get(k), int):
                errors.append(f"meta.dimensions.{k} must be an integer, got {dims.get(k)!r}")

    # meta.language is non-empty array of short tags
    lang = meta.get('language')
    if not isinstance(lang, list) or not lang:
        errors.append(f"meta.language must be a non-empty array, got {lang!r}")
    else:
        for tag in lang:
            if not isinstance(tag, str) or not (2 <= len(tag) <= 8):
                errors.append(f"meta.language tag {tag!r} not a 2-8 char string")

    # meta heterogeneity flags
    if meta.get('parameter_id_style') not in PARAM_ID_STYLES:
        errors.append(f"meta.parameter_id_style={meta.get('parameter_id_style')!r} not in {sorted(PARAM_ID_STYLES)}")
    if meta.get('diagonal_cells') not in DIAGONAL_VALUES:
        errors.append(f"meta.diagonal_cells={meta.get('diagonal_cells')!r} not in {sorted(DIAGONAL_VALUES)}")
    if not meta.get('principle_taxonomy'):
        errors.append("meta.principle_taxonomy is missing")
    if meta.get('interpretation_lineage') not in INTERP_LINEAGE_VALUES:
        errors.append(f"meta.interpretation_lineage={meta.get('interpretation_lineage')!r} not in {sorted(INTERP_LINEAGE_VALUES)}")

    # meta.lineage structure
    lineage = meta.get('lineage')
    if not isinstance(lineage, dict):
        errors.append("meta.lineage must be an object {derived_from, supersedes, identical_to}")

    # principles[].canonical_id and interpretation_lineage
    principles = data.get('principles', {})
    for pid, entry in principles.items():
        cid = entry.get('canonical_id')
        if not isinstance(cid, str) or not CANONICAL_ID_RE.match(cid):
            errors.append(f"principles.{pid}.canonical_id={cid!r} fails pattern ^P_[A-Z][A-Z_]*$")
        lin = entry.get('interpretation_lineage')
        if lin not in INTERP_LINEAGE_VALUES:
            errors.append(f"principles.{pid}.interpretation_lineage={lin!r} not in {sorted(INTERP_LINEAGE_VALUES)}")

    # populated_cells declaration matches actual count
    if isinstance(dims, dict):
        actual = sum(len(row) for row in data.get('matrix', {}).values() if isinstance(row, dict))
        declared = dims.get('populated_cells')
        if declared != actual:
            errors.append(f"meta.dimensions.populated_cells={declared} but matrix has {actual} cells")

    return errors, warnings

def validate_use_case_strict(filepath: str, vocab: dict, valid_ids: set) -> tuple[list, list]:
    errors, warnings = [], []
    data = json.load(open(filepath))
    fname_stem = os.path.splitext(os.path.basename(filepath))[0]

    if isinstance(data, list):
        errors.append(f"top-level is an array; v6 requires one matrix per file (split this file)")
        return errors, warnings
    if not isinstance(data, dict):
        errors.append(f"top-level must be an object, got {type(data).__name__}")
        return errors, warnings

    mid = data.get('matrix_id')
    if mid != fname_stem:
        errors.append(f"matrix_id={mid!r} does not match filename stem {fname_stem!r}")
    if mid not in valid_ids:
        errors.append(f"matrix_id={mid!r} not present in registry")

    for required in ('what_it_is', 'when_to_use', 'selector_tags'):
        if required not in data:
            errors.append(f"missing required v6 field: {required}")

    when = data.get('when_to_use', {})
    if isinstance(when, dict):
        for sub in ('ideal_user_profile', 'best_for', 'not_suitable_for', 'prefer_over_alternatives_when'):
            if sub not in when:
                warnings.append(f"when_to_use.{sub} is missing")
        for i, redirect in enumerate(when.get('skip_in_favor_of', []) or []):
            if not isinstance(redirect, dict):
                errors.append(f"skip_in_favor_of[{i}] not an object")
                continue
            tgt = redirect.get('target_matrix_id')
            if tgt not in valid_ids:
                errors.append(f"skip_in_favor_of[{i}].target_matrix_id={tgt!r} not in registry")
            ifnode = redirect.get('if')
            if ifnode is not None:
                _validate_dsl(ifnode, f'skip_in_favor_of[{i}].if', errors)

    tags = data.get('selector_tags', {})
    if isinstance(tags, dict):
        for k, allowed_field in (('domains', 'domains'),
                                 ('problem_classes', 'problem_classes'),
                                 ('tags', 'tags'),
                                 ('excludes', 'domains')):  # excludes uses domain vocab
            allowed = set(vocab.get(allowed_field, []))
            for v in tags.get(k, []) or []:
                if v not in allowed:
                    errors.append(f"selector_tags.{k}: {v!r} not in vocabulary[{allowed_field}]")

    return errors, warnings

def detect_redirect_cycles(use_cases_dir: str) -> list:
    """Returns list of error strings for cycles in skip_in_favor_of chains."""
    errors = []
    redirects = {}
    if not os.path.isdir(use_cases_dir):
        return errors
    for fn in os.listdir(use_cases_dir):
        if not fn.endswith('.json'):
            continue
        d = json.load(open(os.path.join(use_cases_dir, fn)))
        if not isinstance(d, dict):
            continue  # skip array files; they will be flagged elsewhere
        mid = d.get('matrix_id', os.path.splitext(fn)[0])
        targets = []
        for r in (d.get('when_to_use', {}).get('skip_in_favor_of', []) or []):
            t = r.get('target_matrix_id')
            if t:
                targets.append(t)
        redirects[mid] = targets

    for mid in redirects:
        path = [mid]
        visited = {mid}
        cur = mid
        while True:
            tgts = redirects.get(cur, [])
            if not tgts:
                break
            cur = tgts[0]
            if cur in visited:
                errors.append(f"redirect cycle detected: {' -> '.join(path)} -> {cur}")
                break
            visited.add(cur)
            path.append(cur)
            if len(path) > 4:
                errors.append(f"redirect chain exceeds depth 3: {' -> '.join(path)}")
                break
    return errors

def validate_lineage_identical(matrix_path: str, all_matrices: dict) -> list:
    """If meta.lineage.identical_to lists a target, verify cells hash-identical."""
    errors = []
    d = json.load(open(matrix_path))
    targets = (d.get('meta', {}).get('lineage', {}).get('identical_to') or [])
    src_hash = _hash_cells(d.get('matrix', {}))
    for t in targets:
        target_data = all_matrices.get(t)
        if target_data is None:
            errors.append(f"lineage.identical_to references unknown matrix_id {t!r}")
            continue
        tgt_hash = _hash_cells(target_data.get('matrix', {}))
        if src_hash != tgt_hash:
            errors.append(f"lineage.identical_to claims equality with {t!r} but cell hashes differ")
    return errors

def run_strict() -> int:
    """Run the full v6 strict validation suite over the live corpus. Returns 0 on success."""
    print("Strict mode: validating v6/v1.1 contracts on live corpus.\n")
    if not os.path.exists(VOCAB_PATH):
        print(f"FATAL: vocabulary file missing at {VOCAB_PATH}")
        return 2
    vocab = json.load(open(VOCAB_PATH))

    if not os.path.exists(REGISTRY_PATH):
        print(f"FATAL: registry missing at {REGISTRY_PATH}")
        return 2
    registry = json.load(open(REGISTRY_PATH))
    valid_ids = {m['id'] for m in registry.get('matrices', [])}

    total_errors = 0
    total_warnings = 0

    # Matrix files
    matrix_files = sorted(
        [os.path.join(MATRICES_DIR, f) for f in os.listdir(MATRICES_DIR) if f.endswith('.json')]
        + [os.path.join(MATRICES_DIR, 'redundant', f)
           for f in os.listdir(os.path.join(MATRICES_DIR, 'redundant'))
           if f.endswith('.json')]
    )
    all_matrices = {os.path.splitext(os.path.basename(p))[0]: json.load(open(p)) for p in matrix_files}

    print(f"Matrix files ({len(matrix_files)}):")
    for p in matrix_files:
        legacy_errs, legacy_warns, _ = validate_matrix(p)
        strict_errs, strict_warns = validate_matrix_strict(p, vocab)
        identical_errs = validate_lineage_identical(p, all_matrices)
        all_errs = legacy_errs + strict_errs + identical_errs
        all_warns = legacy_warns + strict_warns
        flag = '!' if all_errs else ('?' if all_warns else ' ')
        print(f"  {flag} {os.path.basename(p):40} errors={len(all_errs)}  warns={len(all_warns)}")
        for e in all_errs:
            print(f"      ERROR: {e}")
        for w in all_warns[:3]:
            print(f"      warn:  {w}")
        if len(all_warns) > 3:
            print(f"      ... and {len(all_warns) - 3} more warnings")
        total_errors += len(all_errs)
        total_warnings += len(all_warns)

    # Use-case files
    print(f"\nUse-case files:")
    if os.path.isdir(USECASES_DIR):
        uc_files = sorted([os.path.join(USECASES_DIR, f)
                           for f in os.listdir(USECASES_DIR) if f.endswith('.json')])
        for p in uc_files:
            errs, warns = validate_use_case_strict(p, vocab, valid_ids)
            flag = '!' if errs else ('?' if warns else ' ')
            print(f"  {flag} {os.path.basename(p):40} errors={len(errs)}  warns={len(warns)}")
            for e in errs:
                print(f"      ERROR: {e}")
            total_errors += len(errs)
            total_warnings += len(warns)

    # Redirect cycles
    print(f"\nRedirect-cycle check:")
    cycle_errs = detect_redirect_cycles(USECASES_DIR)
    if cycle_errs:
        for e in cycle_errs:
            print(f"  ERROR: {e}")
        total_errors += len(cycle_errs)
    else:
        print("  ok (no cycles)")

    # Registry consistency
    print(f"\nRegistry consistency:")
    reg_errs = []
    for entry in registry.get('matrices', []):
        mp = os.path.join(ROOT, entry['matrix_file'])
        if not os.path.exists(mp):
            reg_errs.append(f"matrix_file {entry['matrix_file']!r} for id={entry['id']!r} does not exist")
    for e in reg_errs:
        print(f"  ERROR: {e}")
    total_errors += len(reg_errs)
    if not reg_errs:
        print("  ok")

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_errors} errors, {total_warnings} warnings")
    return 0 if total_errors == 0 else 1


def run_legacy(files):
    all_passed = True
    for filepath in files:
        print(f"\n{'='*60}\nValidating: {os.path.basename(filepath)}\n{'='*60}")
        try:
            errors, warnings, stats = validate_matrix(filepath)
        except json.JSONDecodeError as e:
            print(f"  FATAL: Invalid JSON - {e}")
            all_passed = False
            continue
        if errors:
            all_passed = False
            print(f"\n  ERRORS ({len(errors)}):")
            for e in errors[:20]:
                print(f"    - {e}")
        if warnings:
            print(f"\n  WARNINGS ({len(warnings)}):")
            for w in warnings:
                print(f"    - {w}")
        for matrix_key, s in stats.items():
            print(f"\n  STATS [{matrix_key}]: cells={s['total_populated_cells']} "
                  f"sparsity={s['sparsity_pct']}% avg_p/cell={s['avg_principles_per_cell']}")
        print(f"\n  RESULT: {'PASSED' if not errors else 'FAILED'}")
    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description='Validate TRIZ matrix files.')
    parser.add_argument('--strict', action='store_true',
                        help='v6/v1.1 contracts: validates matrices, use-cases, registry, vocabulary, redirect cycles, lineage hashes')
    parser.add_argument('files', nargs='*', help='specific files (legacy mode only)')
    args = parser.parse_args()

    if args.strict:
        sys.exit(run_strict())

    if args.files:
        files = args.files
    else:
        files = sorted([os.path.join(MATRICES_DIR, f)
                        for f in os.listdir(MATRICES_DIR) if f.endswith('.json')])
    sys.exit(run_legacy(files))


if __name__ == '__main__':
    main()
