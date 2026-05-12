"""Regenerate registry.json from current matrix files. Run after any matrix-meta change."""

import hashlib
import json
import os
import sys

ROOT     = '/Users/constantinzemelman/Projects/Triz_matrixes'
MATRICES = os.path.join(ROOT, 'matrices')

def hash_file(p: str) -> str:
    return 'sha256:' + hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

def short_summary(meta: dict, cells: int) -> str:
    name = meta.get('name', '')
    yr = meta.get('year', '')
    cells_str = f'{cells} cells' if cells else 'shell only (no cells)'
    return f'{name} ({yr}). {cells_str}.'

def collect(dirpath: str, status_default: str = None) -> list:
    out = []
    for fn in sorted(os.listdir(dirpath)):
        if not fn.endswith('.json'):
            continue
        p = os.path.join(dirpath, fn)
        d = json.load(open(p))
        meta = d.get('meta', {})
        rel = os.path.relpath(p, ROOT)
        dims = meta.get('dimensions', {})
        cells = dims.get('populated_cells', 0) if isinstance(dims, dict) else 0
        mid = meta.get('id', os.path.splitext(fn)[0])
        entry = {
            'id':                     mid,
            'matrix_file':            rel,
            'status':                 meta.get('status', status_default or 'unknown'),
            'language':               meta.get('language', ['en']),
            'dimensions':             dims if isinstance(dims, dict) else {},
            'parameter_id_style':     meta.get('parameter_id_style', 'numeric'),
            'diagonal_cells':         meta.get('diagonal_cells', 'excluded'),
            'principle_taxonomy':     meta.get('principle_taxonomy', 'altshuller-40'),
            'interpretation_lineage': meta.get('interpretation_lineage', 'altshuller-40'),
            'lineage':                meta.get('lineage', {}),
            'content_hash':           hash_file(p),
            'summary':                short_summary(meta, cells),
        }
        # Use-case file pointer (only for non-redundant)
        if (status_default or meta.get('status')) != 'identical-duplicate':
            uc = f'use_cases/{mid}.json'
            if os.path.exists(os.path.join(ROOT, uc)):
                entry['use_case_file'] = uc
        out.append(entry)
    return out

def main():
    active    = collect(MATRICES)
    redundant = collect(os.path.join(MATRICES, 'redundant'), status_default='identical-duplicate')

    registry = {
        'schema_version':         '1.1',
        'generated':              '2026-05-04',
        'storage_design_version': '1.1',
        'matrices':               active + redundant,
        'notes': ('Regenerated after Phase 0 substrate completion. selector_tags '
                  'and skip_in_favor_of redirects are populated in '
                  'use_cases/<matrix_id>.json files. canonical_id and '
                  'interpretation_lineage are set on every principle entry. '
                  'Run `python3 validate_matrix.py --strict` to re-verify.'),
    }
    out = os.path.join(ROOT, 'registry.json')
    with open(out, 'w') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    from collections import Counter
    c = Counter(m['status'] for m in registry['matrices'])
    print(f'wrote {out}')
    print(f'total entries: {len(registry["matrices"])}')
    for status, n in sorted(c.items()):
        print(f'  {status:25} {n}')

if __name__ == '__main__':
    sys.exit(main())
