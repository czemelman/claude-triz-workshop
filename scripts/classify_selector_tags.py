"""
Hand-classified selector_tags + skip_in_favor_of redirects per matrix.

The classifications below are derived from each matrix's existing use-case prose
(now archived under use_cases/legacy/) plus design knowledge from
matrix_storage_design.md and triz_workshop_design.md v6.

All values draw from selector_tags_vocabulary.json (amendment 2). Adding new
values requires updating the vocabulary first.
"""

import json
import os
import sys

ROOT      = '/Users/constantinzemelman/Projects/Triz_matrixes/prizm/data'
USE_CASES = os.path.join(ROOT, 'use_cases')

# ---------------------------------------------------------------------------
# Per-matrix classifications.
# ---------------------------------------------------------------------------

CLASSIFICATIONS = {
    "altshuller_39x39": {
        "domains": ["mechanical", "manufacturing", "industrial-design", "materials-science",
                    "aerospace", "automotive", "civil", "structural", "process-engineering",
                    "chemical", "consumer-product", "general-engineering"],
        "problem_classes": ["engineering-contradiction"],
        "tags": ["physical-product", "patent-derived", "canonical", "teaching-baseline",
                 "structural-integrity-focus", "manufacturing-trade-offs"],
        "excludes": ["software", "ai-ml", "cybersecurity", "ux", "service",
                     "governance", "bio", "pharmaceutical", "fintech"],
        "skip_in_favor_of": [
            {"target_matrix_id": "triz_ai_50x50",
             "if": {"any_of": [
                 {"exotic_signal": "security"},
                 {"exotic_signal": "compatibility"},
                 {"exotic_signal": "sustainability"},
                 {"exotic_signal": "noise"},
                 {"exotic_signal": "harmful-emissions"},
                 {"exotic_signal": "safety"},
                 {"exotic_signal": "scalability"},
                 {"exotic_signal": "controllability"},
                 {"exotic_signal": "aesthetics"},
                 {"exotic_signal": "information-capacity"}]}},
            {"target_matrix_id": "biotriz_6x6_bio",
             "if": {"exotic_signal": "bio-analogy"}},
            {"target_matrix_id": "drug_safety_18x18",
             "if": {"all_of": [{"domain_signal": "pharmaceutical"},
                               {"exotic_signal": "governance"}]}},
            {"target_matrix_id": "healthcare_servqual",
             "if": {"all_of": [{"domain_signal": "healthcare"},
                               {"exotic_signal": "service-experience"}]}},
        ],
    },
    "altshuller_russian_original": {
        "domains": ["mechanical", "manufacturing", "industrial-design", "materials-science",
                    "aerospace", "automotive", "civil", "structural", "process-engineering",
                    "chemical", "consumer-product", "general-engineering"],
        "problem_classes": ["engineering-contradiction"],
        "tags": ["physical-product", "patent-derived", "canonical",
                 "russian-names", "teaching-baseline"],
        "excludes": ["software", "ai-ml", "cybersecurity", "ux", "service",
                     "governance", "bio", "pharmaceutical", "fintech"],
        # No skip_in_favor_of: in v0.1 (English-only), Stage A's language filter
        # already drops this matrix; redirect would create a static cycle with
        # altshuller_39x39 → triz_ai_50x50.
        "skip_in_favor_of": [],
    },
    "heinrich_39x39": {
        "domains": ["mechanical", "manufacturing", "structural", "energy-systems",
                    "aerospace", "automotive", "general-engineering"],
        "problem_classes": ["engineering-contradiction"],
        "tags": ["physical-product", "curated-subset", "structural-integrity-focus",
                 "ariz-companion"],
        "excludes": ["software", "ai-ml", "cybersecurity", "ux", "service",
                     "governance", "bio", "pharmaceutical"],
        # No redirect: Heinrich is a deliberately curated 109-cell subset; users
        # who want fuller coverage should select altshuller_39x39 explicitly via
        # Stage D scoring. A redirect would chain into altshuller's own redirects.
        "skip_in_favor_of": [],
    },
    "mann_matrix2003_48x48": {
        "domains": ["mechanical", "manufacturing", "industrial-design",
                    "consumer-product", "general-engineering"],
        "problem_classes": ["engineering-contradiction"],
        "tags": ["patent-derived", "patent-1985-2002", "extended-50-param", "shell-only"],
        "excludes": ["software", "ai-ml", "cybersecurity", "ux", "service",
                     "governance", "bio", "pharmaceutical"],
        # No redirect: Stage A drops shell matrices unless --matrix= override.
        # If user explicitly requested Mann, honoring that beats redirecting.
        "skip_in_favor_of": [],
    },
    "triz_ai_50x50": {
        "domains": ["mechanical", "manufacturing", "software", "ai-ml", "cybersecurity",
                    "ux", "consumer-product", "energy-systems", "data-systems",
                    "biomedical-device", "general-engineering"],
        "problem_classes": ["engineering-contradiction"],
        "tags": ["extended-50-param", "llm-generated", "ai-curated", "experimental"],
        "excludes": ["governance", "service", "pharmaceutical", "bio"],
        # No reverse redirect: would create a static cycle with altshuller→triz_ai.
        # The exotic_signal scoring already pushes triz_ai down when no exotic
        # signal is present; Stage D handles this without an explicit redirect.
        "skip_in_favor_of": [],
    },
    "drug_safety_18x18": {
        "domains": ["governance", "regulatory", "public-health", "policy",
                    "compliance", "pharmaceutical", "drug-safety"],
        "problem_classes": ["governance-tension", "multi-stakeholder-coordination",
                            "regulatory-design"],
        "tags": ["governance-reframed"],
        "excludes": ["mechanical", "manufacturing", "software", "ai-ml",
                     "consumer-product", "biomedical-device"],
        # No redirect: excludes already drop this matrix when domain doesn't
        # match governance/regulatory/policy. A redirect would chain into
        # altshuller's own redirects and create a static path > depth 3.
        "skip_in_favor_of": [],
    },
    "healthcare_servqual": {
        "domains": ["healthcare", "service", "telehealth", "hospitality"],
        "problem_classes": ["service-quality-gap"],
        "tags": ["service-quality-hybrid"],
        "excludes": ["mechanical", "manufacturing", "ai-ml", "cybersecurity",
                     "consumer-product", "governance", "pharmaceutical", "bio"],
        # No redirect: excludes already drop this matrix when domain doesn't
        # match service/healthcare/telehealth.
        "skip_in_favor_of": [],
    },
    "biotriz_6x6_bio": {
        "domains": ["bio", "biology", "biomimetics", "ecology", "sustainability",
                    "biomedical-device"],
        "problem_classes": ["biological-design", "engineering-contradiction"],
        "tags": ["biology-derived", "operational-fields-6"],
        "excludes": ["governance", "service", "pharmaceutical"],
        # No redirect: when bio-analogy is signaled this matrix wins via Stage D;
        # when it's not, biotriz_6x6_tech's bio exclude in domain_signals handles
        # the reverse. Mutual redirect would be a static cycle.
        "skip_in_favor_of": [],
    },
    "biotriz_6x6_tech": {
        "domains": ["mechanical", "manufacturing", "general-engineering"],
        "problem_classes": ["engineering-contradiction"],
        "tags": ["technology-derived", "operational-fields-6"],
        "excludes": ["governance", "service", "pharmaceutical", "bio"],
        # No redirect: Stage A excludes drop this when bio domain signaled;
        # Stage D scoring promotes altshuller_39x39 when it scores higher.
        "skip_in_favor_of": [],
    },
    "biotriz_24x24": {
        "domains": ["bio", "biology", "biomimetics", "ecology"],
        "problem_classes": ["biological-design"],
        "tags": ["biology-derived", "operational-fields-6"],
        "excludes": ["governance", "service", "pharmaceutical"],
        # 24x24 is partially redundant (same 36 cells as biotriz_6x6_bio plus
        # supplementary data). Redirect: when bio is signaled, prefer the
        # primary 6x6 split; this terminates (biotriz_6x6_bio has no redirects).
        "skip_in_favor_of": [
            {"target_matrix_id": "biotriz_6x6_bio",
             "if": {"exotic_signal": "bio-analogy"}},
        ],
    },
    "innovatetriz_extended": {
        "domains": ["mechanical", "manufacturing", "consumer-product", "general-engineering"],
        "problem_classes": ["engineering-contradiction"],
        "tags": ["bilingual", "experimental"],
        "excludes": ["governance", "service", "pharmaceutical", "bio", "ai-ml"],
        # No redirect: Stage A's English-only language filter already drops this
        # in v0.1. When --lang=zh ships, Chinese users can use this directly.
        "skip_in_favor_of": [],
    },
}


def main():
    updated = 0
    for mid, c in CLASSIFICATIONS.items():
        path = os.path.join(USE_CASES, f'{mid}.json')
        if not os.path.exists(path):
            print(f'  ! missing use-case file: {path}')
            continue
        d = json.load(open(path))
        d['selector_tags'] = {
            'domains':         c['domains'],
            'problem_classes': c['problem_classes'],
            'tags':            c['tags'],
            'excludes':        c['excludes'],
        }
        d.setdefault('when_to_use', {})['skip_in_favor_of'] = c['skip_in_favor_of']
        # Drop legacy fields now that they're absorbed/normalized
        d.pop('_legacy_primary_domains', None)
        d.pop('_legacy_secondary_domains', None)
        d.get('when_to_use', {}).pop('_skip_in_favor_of_narrative', None)
        with open(path, 'w') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        print(f'  updated {mid:30}  domains={len(c["domains"]):>2}  '
              f'tags={len(c["tags"]):>2}  excludes={len(c["excludes"]):>2}  '
              f'redirects={len(c["skip_in_favor_of"])}')
        updated += 1

    print(f'\n{updated} files updated.')

if __name__ == '__main__':
    sys.exit(main())
