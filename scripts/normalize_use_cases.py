"""
Normalize use-case files in `use_cases/` to v6 §3.4 schema.

Input files (heterogeneous shapes):
  - altshuller_39x39_use_cases.json       (matrix=, primary/secondary_domains, ...)
  - altshuller_russian_use_cases.json     (same shape as altshuller_39x39)
  - heinrich_39x39_use_cases.json         (matrix_ref=, coverage_summary, domain_fit, ...)
  - mann_matrix2003_use_cases.json        (meta=, analysis=, use_cases=, ...)
  - triz_ai_50x50_use_cases.json          (matrix_ref=, domain_fit, when_to_use, when_not_to_use)
  - domain_specific_use_cases.json        (ARRAY of 5 matrix entries)

Output: one v6-shaped file per matrix_id at use_cases/<matrix_id>.json.

For matrix ids in the registry that have NO source use-case file
(biotriz_6x6_bio, biotriz_6x6_tech), emit a stub derived from the legacy
biotriz_6x6 entry in domain_specific_use_cases.json.

Schema: every output file has matrix_id, schema_version=1, what_it_is,
when_to_use{ideal_user_profile, best_for, not_suitable_for,
prefer_over_alternatives_when, skip_in_favor_of[]}, selector_tags{...},
coverage{}, strengths[], weaknesses[].

selector_tags arrays are populated empty here. A4 fills them with
controlled-vocab values.
"""

import json
import os
import sys
from typing import Any

ROOT      = '/Users/constantinzemelman/Projects/Triz_matrixes'
USE_CASES = os.path.join(ROOT, 'use_cases')
REGISTRY  = json.load(open(os.path.join(ROOT, 'registry.json')))
VALID_IDS = {m['id'] for m in REGISTRY['matrices'] if m.get('status') != 'identical-duplicate'}

def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] is not None and d[k] != '':
            return d[k]
    return default

def _to_v6(src: dict, matrix_id: str) -> dict:
    """Best-effort conversion of any of the heterogeneous source shapes to v6."""
    name = _first(src, 'matrix_name', default=matrix_id)
    primary   = _first(src, 'primary_domains', default=[])
    secondary = _first(src, 'secondary_domains', default=[])

    # Strengths/weaknesses arrays
    strengths  = _first(src, 'strength_areas', 'strengths', default=[])
    weaknesses = _first(src, 'weakness_areas', 'limitations', 'weaknesses', default=[])
    if isinstance(weaknesses, dict):
        # heinrich nests under domain_fit etc.; flatten
        weaknesses = [{'area': k, 'why': v if isinstance(v, str) else json.dumps(v)}
                      for k, v in weaknesses.items()]
    if isinstance(strengths, dict):
        strengths = [{'area': k, 'why': v if isinstance(v, str) else json.dumps(v)}
                     for k, v in strengths.items()]

    # when_to_use object
    ideal = _first(src, 'ideal_user_profile')
    best_for         = _first(src, 'best_for', default=[])
    not_suitable_for = _first(src, 'not_suitable_for', 'when_not_to_use', default=[])
    prefer_when      = _first(src, 'when_to_prefer', 'ideal_approach', default=None)
    skip_when_text   = _first(src, 'when_to_skip', default=None)

    # heinrich/triz_ai have nested when_to_use
    nested_wtu = src.get('when_to_use', {})
    if isinstance(nested_wtu, dict):
        ideal = ideal or nested_wtu.get('ideal_user_profile')
        if not best_for:
            best_for = nested_wtu.get('best_for', []) or nested_wtu.get('use_when', [])
        if not prefer_when:
            prefer_when = nested_wtu.get('prefer_over_alternatives_when') or nested_wtu.get('summary')

    when_to_use = {
        'ideal_user_profile': ideal or '',
        'best_for': best_for or [],
        'not_suitable_for': not_suitable_for or [],
        'prefer_over_alternatives_when': prefer_when or '',
        'skip_in_favor_of': [],   # populated in A4
    }
    if skip_when_text:
        when_to_use['_skip_in_favor_of_narrative'] = skip_when_text  # preserved as A4 input

    # what_it_is — synthesize one paragraph
    what = _first(src, 'what_it_is', 'summary')
    if not what:
        # Try to lift from common nested locations
        df = src.get('domain_fit', {})
        if isinstance(df, dict):
            what = df.get('summary') or df.get('description')
    if not what:
        # Generate a minimal description from the matrix name and primary domain
        primary_str = ', '.join(primary) if primary else 'general engineering'
        what = f'TRIZ contradiction matrix used for {primary_str} problem framing.'

    # Coverage
    coverage = _first(src, 'coverage_stats', 'coverage_summary',
                      'statistical_profile', 'coverage', default={})
    if not isinstance(coverage, dict):
        coverage = {'note': str(coverage)}

    # selector_tags — empty stubs (populated in A4)
    selector_tags = {
        'domains': [],
        'problem_classes': [],
        'tags': [],
        'excludes': [],
    }

    return {
        'matrix_id': matrix_id,
        'schema_version': 1,
        'what_it_is': what,
        'when_to_use': when_to_use,
        'selector_tags': selector_tags,
        'coverage': coverage,
        'strengths': strengths if isinstance(strengths, list) else [],
        'weaknesses': weaknesses if isinstance(weaknesses, list) else [],
        '_legacy_primary_domains': primary,
        '_legacy_secondary_domains': secondary,
    }

# ---- Per-source loaders ----

def load_old(path: str) -> dict:
    return json.load(open(path))

def main():
    out_files = {}  # matrix_id -> v6 dict

    # 1. Single-matrix per file (5 files)
    single_files = {
        'altshuller_39x39':           f'{USE_CASES}/altshuller_39x39_use_cases.json',
        'altshuller_russian_original': f'{USE_CASES}/altshuller_russian_use_cases.json',
        'heinrich_39x39':             f'{USE_CASES}/heinrich_39x39_use_cases.json',
        'mann_matrix2003_48x48':      f'{USE_CASES}/mann_matrix2003_use_cases.json',
        'triz_ai_50x50':              f'{USE_CASES}/triz_ai_50x50_use_cases.json',
    }
    for mid, path in single_files.items():
        if not os.path.exists(path):
            print(f'  ! source missing: {path}')
            continue
        src = load_old(path)
        out_files[mid] = _to_v6(src, mid)
        print(f'  loaded single source: {mid}')

    # 2. Domain-specific array (5 entries)
    arr_path = f'{USE_CASES}/domain_specific_use_cases.json'
    if os.path.exists(arr_path):
        arr = json.load(open(arr_path))
        # Each entry's `matrix` is the matrix_id
        for item in arr:
            mid_src = item.get('matrix')
            # biotriz_6x6 in legacy file → split into bio and tech
            if mid_src == 'biotriz_6x6':
                # Build bio version from the legacy entry
                bio = _to_v6(item, 'biotriz_6x6_bio')
                bio['what_it_is'] = (
                    'BioTRIZ biology-derived contradiction matrix. Six operational fields '
                    '(substance, structure, space, time, energy, information). Cells encode '
                    'principles abstracted from biological mechanisms; use when applying '
                    'biomimetic analogies to engineering or systems problems.'
                )
                out_files['biotriz_6x6_bio'] = bio
                print(f'  derived biotriz_6x6_bio from legacy biotriz_6x6 entry')
                # And a tech version
                tech = _to_v6(item, 'biotriz_6x6_tech')
                tech['what_it_is'] = (
                    'BioTRIZ technology-derived comparison matrix. Same six operational fields '
                    'as the biology submatrix; cells encode engineering-domain solutions. Use '
                    'as a baseline against biotriz_6x6_bio when comparing biological vs. '
                    'engineering framings of the same contradiction.'
                )
                out_files['biotriz_6x6_tech'] = tech
                print(f'  derived biotriz_6x6_tech from legacy biotriz_6x6 entry')
            elif mid_src in VALID_IDS:
                out_files[mid_src] = _to_v6(item, mid_src)
                print(f'  loaded array entry: {mid_src}')
            else:
                # Skip biotriz_24x24 if not in registry, etc.
                if mid_src == 'biotriz_24x24':
                    out_files[mid_src] = _to_v6(item, mid_src)
                    print(f'  loaded array entry: {mid_src}')
                else:
                    print(f'  ! unknown matrix_id in array: {mid_src}')

    # 3. Write outputs (use-case file per id)
    print(f'\nWriting {len(out_files)} use-case files:\n')
    for mid, body in sorted(out_files.items()):
        out_path = f'{USE_CASES}/{mid}.json'
        with open(out_path, 'w') as f:
            json.dump(body, f, indent=2, ensure_ascii=False)
        print(f'  wrote {out_path}')

    # 4. Move old/legacy use-case files to use_cases/legacy/ for archival
    legacy_dir = f'{USE_CASES}/legacy'
    os.makedirs(legacy_dir, exist_ok=True)
    legacy_files = [
        'altshuller_39x39_use_cases.json',
        'altshuller_russian_use_cases.json',
        'heinrich_39x39_use_cases.json',
        'mann_matrix2003_use_cases.json',
        'triz_ai_50x50_use_cases.json',
        'domain_specific_use_cases.json',
    ]
    print(f'\nArchiving {len(legacy_files)} legacy files to {legacy_dir}/:\n')
    for fn in legacy_files:
        src = f'{USE_CASES}/{fn}'
        dst = f'{legacy_dir}/{fn}'
        if os.path.exists(src):
            os.rename(src, dst)
            print(f'  moved {fn}')

    print(f'\ndone. {len(out_files)} v6 files created; legacy archived.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
