"""
Add canonical_id and interpretation_lineage to every principle entry in every matrix file.

Strategy:
- Primary: lookup by integer principle ID (position in the Altshuller-40 ordering).
  All matrices in this corpus use the standard "1"..."40" position keys for principles
  even when they use a subset (healthcare_servqual uses {1,2,4,10,...}; drug_safety
  omits 7). Position is therefore the most reliable canonical-id key.
- Secondary fallback: lookup by normalized principle name (handles renames like
  "The other way round" vs "Inversion" vs "Doing it in reverse"). Reports any
  unmapped principles for manual review.

interpretation_lineage on each principle defaults to meta.interpretation_lineage.
This is redundant-by-default but explicit, allowing future per-principle overrides
(e.g. a matrix that mostly uses altshuller-40 but has one principle reinterpreted).

Writes back atomically (write to .tmp, rename).
"""

import json
import os
import sys
import glob
import tempfile
from typing import Optional

ROOT = '/Users/constantinzemelman/Projects/Triz_matrixes/prizm/data/matrices'

# The Altshuller-40 canonical ordering (1-indexed). Each entry: (id, canonical_id, primary_name).
# Canonical IDs follow the convention P_<UPPERCASE_NAME_WITH_UNDERSCORES>.
ALTSHULLER_40 = [
    (1,  "P_SEGMENTATION",                "Segmentation"),
    (2,  "P_TAKING_OUT",                  "Taking out"),
    (3,  "P_LOCAL_QUALITY",               "Local quality"),
    (4,  "P_ASYMMETRY",                   "Asymmetry"),
    (5,  "P_MERGING",                     "Merging"),
    (6,  "P_UNIVERSALITY",                "Universality"),
    (7,  "P_NESTED_DOLL",                 "Nested doll"),
    (8,  "P_ANTI_WEIGHT",                 "Anti-weight"),
    (9,  "P_PRELIMINARY_ANTI_ACTION",     "Preliminary anti-action"),
    (10, "P_PRELIMINARY_ACTION",          "Preliminary action"),
    (11, "P_BEFOREHAND_CUSHIONING",       "Beforehand cushioning"),
    (12, "P_EQUIPOTENTIALITY",            "Equipotentiality"),
    (13, "P_THE_OTHER_WAY_ROUND",         "The other way round"),
    (14, "P_SPHEROIDALITY",               "Spheroidality"),
    (15, "P_DYNAMICS",                    "Dynamics"),
    (16, "P_PARTIAL_OR_EXCESSIVE",        "Partial or excessive actions"),
    (17, "P_ANOTHER_DIMENSION",           "Another dimension"),
    (18, "P_MECHANICAL_VIBRATION",        "Mechanical vibration"),
    (19, "P_PERIODIC_ACTION",             "Periodic action"),
    (20, "P_CONTINUITY_OF_USEFUL_ACTION", "Continuity of useful action"),
    (21, "P_SKIPPING",                    "Skipping"),
    (22, "P_BLESSING_IN_DISGUISE",        "Blessing in disguise"),
    (23, "P_FEEDBACK",                    "Feedback"),
    (24, "P_INTERMEDIARY",                "Intermediary"),
    (25, "P_SELF_SERVICE",                "Self-service"),
    (26, "P_COPYING",                     "Copying"),
    (27, "P_CHEAP_SHORT_LIVING",          "Cheap short-living objects"),
    (28, "P_MECHANICS_SUBSTITUTION",      "Mechanics substitution"),
    (29, "P_PNEUMATICS_HYDRAULICS",       "Pneumatics and hydraulics"),
    (30, "P_FLEXIBLE_SHELLS",             "Flexible shells and thin films"),
    (31, "P_POROUS_MATERIALS",            "Porous materials"),
    (32, "P_COLOR_CHANGES",               "Color changes"),
    (33, "P_HOMOGENEITY",                 "Homogeneity"),
    (34, "P_DISCARDING_RECOVERING",       "Discarding and recovering"),
    (35, "P_PARAMETER_CHANGES",           "Parameter changes"),
    (36, "P_PHASE_TRANSITIONS",           "Phase transitions"),
    (37, "P_THERMAL_EXPANSION",           "Thermal expansion"),
    (38, "P_STRONG_OXIDANTS",             "Strong oxidants"),
    (39, "P_INERT_ATMOSPHERE",            "Inert atmosphere"),
    (40, "P_COMPOSITE_MATERIALS",         "Composite materials"),
]

ID_TO_CANONICAL = {pid: cid for pid, cid, _ in ALTSHULLER_40}

# Name-normalization fallback: lowercase, strip parentheticals, drop separators.
def _normalize(name: str) -> str:
    s = name.lower().strip()
    # Drop everything in parentheses: "Spheroidality (Curvature)" -> "spheroidality"
    while '(' in s and ')' in s:
        i, j = s.index('('), s.index(')')
        if i < j:
            s = (s[:i] + s[j+1:]).strip()
        else:
            break
    # Replace common separators with space
    for sep in ['/', ' - ', '-']:
        s = s.replace(sep, ' ')
    s = ' '.join(s.split())  # collapse whitespace
    return s

NAME_TO_CANONICAL = {}
for pid, cid, name in ALTSHULLER_40:
    NAME_TO_CANONICAL[_normalize(name)] = cid

# Manually map known synonyms to canonical IDs.
NAME_SYNONYMS = {
    "inversion":               "P_THE_OTHER_WAY_ROUND",
    "doing it in reverse":     "P_THE_OTHER_WAY_ROUND",
    "extraction":              "P_TAKING_OUT",
    "mediator":                "P_INTERMEDIARY",
    "counterweight":           "P_ANTI_WEIGHT",
    "consolidation":           "P_MERGING",
    "combining":               "P_MERGING",
    "nesting":                 "P_NESTED_DOLL",
    "rushing through":         "P_SKIPPING",
    "rejection and regeneration of parts": "P_DISCARDING_RECOVERING",
    "translation of properties": "P_PARAMETER_CHANGES",
    "replacement of mechanical system": "P_MECHANICS_SUBSTITUTION",
    "change of colour":        "P_COLOR_CHANGES",
    "colour changes":          "P_COLOR_CHANGES",
    "prior action":            "P_PRELIMINARY_ACTION",
    "conversion of harm into benefit": "P_BLESSING_IN_DISGUISE",
    "turn lemons into lemonade": "P_BLESSING_IN_DISGUISE",
    "loss of curvature":       "P_SPHEROIDALITY",
    "curvature":               "P_SPHEROIDALITY",
    "accelerated oxidation":   "P_STRONG_OXIDANTS",
    "dynamisation":            "P_DYNAMICS",
}

def lookup(principle_id: str, name: str) -> Optional[str]:
    """Return canonical_id or None if no mapping."""
    # Primary: by ID position
    try:
        pid_int = int(principle_id)
        if pid_int in ID_TO_CANONICAL:
            return ID_TO_CANONICAL[pid_int]
    except (ValueError, TypeError):
        pass
    # Secondary: by normalized name (try whole-name then each chunk after ' / ')
    norm = _normalize(name)
    if norm in NAME_TO_CANONICAL:
        return NAME_TO_CANONICAL[norm]
    if norm in NAME_SYNONYMS:
        return NAME_SYNONYMS[norm]
    # Try splitting compound names "X / Y" - return canonical of first matched part
    for part in norm.split(' '):
        if part in NAME_TO_CANONICAL:
            return NAME_TO_CANONICAL[part]
    return None


def atomic_write(path: str, data) -> None:
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def process_file(path: str) -> dict:
    """Return a per-file report."""
    d = json.load(open(path))
    matrix_id = d.get('meta', {}).get('id', os.path.splitext(os.path.basename(path))[0])
    default_lineage = d.get('meta', {}).get('interpretation_lineage', 'altshuller-40')
    principles = d.get('principles', {})

    added_canonical = 0
    added_lineage = 0
    unmapped = []
    for pid, entry in principles.items():
        if 'canonical_id' not in entry or not entry['canonical_id']:
            cid = lookup(pid, entry.get('name', ''))
            if cid is None:
                # Last-resort fallback: synthesize from the name
                fallback = 'P_' + ''.join(c if c.isalnum() else '_' for c in entry.get('name', '').upper()).strip('_')
                fallback = '_'.join(filter(None, fallback.split('_')))
                cid = fallback
                unmapped.append((pid, entry.get('name', ''), cid))
            entry['canonical_id'] = cid
            added_canonical += 1
        if 'interpretation_lineage' not in entry or not entry['interpretation_lineage']:
            entry['interpretation_lineage'] = default_lineage
            added_lineage += 1

    atomic_write(path, d)

    return {
        'matrix_id': matrix_id,
        'principles_processed': len(principles),
        'added_canonical_id': added_canonical,
        'added_interpretation_lineage': added_lineage,
        'unmapped': unmapped,
        'default_lineage': default_lineage,
    }


def main():
    files = sorted(glob.glob(f'{ROOT}/*.json')) + sorted(glob.glob(f'{ROOT}/redundant/*.json'))
    total_canonical = 0
    total_lineage = 0
    total_unmapped = 0
    print(f'Processing {len(files)} matrix files...\n')
    for p in files:
        r = process_file(p)
        flag = '  '
        if r['unmapped']:
            flag = '! '
            total_unmapped += len(r['unmapped'])
        print(f'{flag}{r["matrix_id"]:30} +{r["added_canonical_id"]:>3} canonical_id, '
              f'+{r["added_interpretation_lineage"]:>3} interpretation_lineage '
              f'(lineage={r["default_lineage"]})')
        for pid, name, cid in r['unmapped']:
            print(f'    UNMAPPED: id={pid} name={name!r} -> fallback {cid}')
        total_canonical += r['added_canonical_id']
        total_lineage += r['added_interpretation_lineage']

    print()
    print(f'Total canonical_id additions: {total_canonical}')
    print(f'Total interpretation_lineage additions: {total_lineage}')
    print(f'Total unmapped (used name-derived fallback): {total_unmapped}')
    return 0 if total_unmapped == 0 else 0  # never error; just report


if __name__ == '__main__':
    sys.exit(main())
