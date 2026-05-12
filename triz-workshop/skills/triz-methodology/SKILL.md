---
name: triz-methodology
description: Background on TRIZ contradiction-resolution methodology, including the 39 standard parameters, 40 inventive principles, common failure modes (Souchkov's 10-15% mapping rate), the difference between engineering and physical contradictions, the per-matrix interpretation_lineage taxonomy (altshuller-40, biotriz-40, drug-safety-reframed, triz-ai-extended), language tag handling, and when to consider ARIZ as an alternative. Load when working on TRIZ problem decomposition, parameter mapping, or principle interpretation.
---

# TRIZ methodology

This skill is the shared methodology background for every subagent in the `triz-workshop` plugin. It is a reference, not a runbook — each subagent's own system prompt tells it what to do; this skill explains the background it needs to do it well.

This skill does NOT contain matrix data. The 39 parameters and 40 principles are described here only as orientation; their authoritative definitions live in the matrix files themselves (each matrix declares its own parameter and principle blocks, possibly differing from the classical Altshuller set).

---

## 1. TRIZ in one paragraph

TRIZ (Теория решения изобретательских задач, Russian acronym for "theory of inventive problem solving") was developed by Genrikh Altshuller and collaborators starting in the late 1940s, after analysing tens of thousands of patents to identify recurring patterns in how inventors resolved technical contradictions. The core artifact most associated with TRIZ — the "contradiction matrix" — pairs 39 standard engineering parameters along two axes (the parameter being improved vs. the parameter that worsens as a side effect) and, for each pair, lists 1–4 of the 40 inventive principles statistically most likely to resolve that contradiction in the patent corpus. Altshuller himself eventually advised against the matrix as the primary tool — he came to prefer ARIZ (Algorithm of Inventive Problem Solving), a longer structured procedure that the matrix was originally supposed to be a quick shortcut for. The matrix remains in wide use because it is fast and broadly applicable; this plugin treats it as one tool among several, not the definitive one.

---

## 2. Contradiction types — engineering vs physical

This distinction is load-bearing. The matrix is shaped for one of these and not the other.

### Engineering contradictions (the matrix's natural shape)

An **engineering contradiction** has TWO distinct parameters in tension: improving parameter A worsens parameter B. Examples:

- "Lower car weight" (improving: weight) "reduces crash safety" (worsening: structural integrity).
- "Faster card authorisation" (improving: speed) "reduces fraud-rule recall" (worsening: detection capability).
- "Higher reactor temperature" (improving: yield) "increases corrosion" (worsening: durability).

The matrix's two axes, by construction, encode this two-parameter shape. Mapping is "find the parameter id for A on the rows, find the parameter id for B on the columns, read the cell."

### Physical contradictions (the matrix is the wrong tool)

A **physical contradiction** has ONE parameter that must take TWO opposing states. Examples:

- "The cache must be both hot (for read latency) and cold (for write durability)."
- "The policy must both block and allow the same request, depending on tenant context."
- "The bridge cable must be both long (to span) and short (to resist flex)."

There is no two-axis pair to look up — the matrix has nothing to say. Resolution techniques for physical contradictions live in ARIZ and the 11 separation principles (separation in time, in space, on condition, between system and environment, etc.). The plugin does not implement those in v0.1; when a physical contradiction is detected, the no-clean-mapping branch should fire and the report should suggest ARIZ or reformulation.

When framing an input, the framer must label the contradiction type honestly. The matrix-mapper may still attempt a forced mapping for a physical contradiction; the no-clean-mapping branch will catch it.

---

## 3. The 39 standard parameters

Brief reference only. **Authoritative definitions live in each matrix's parameters block.** Different matrices may use the classical Altshuller 39, an extended set (e.g. `triz_ai_50x50` adds AI/ML axes), a specialised set (e.g. `healthcare_servqual` uses prefixed `S1`-style ids for service-quality dimensions), or a biological reframing (BioTRIZ's 6×6 matrices have only 6 axes).

The classical Altshuller 39 (numbered 1–39):

1. Weight of moving object · 2. Weight of stationary object · 3. Length of moving object · 4. Length of stationary object · 5. Area of moving object · 6. Area of stationary object · 7. Volume of moving object · 8. Volume of stationary object · 9. Speed · 10. Force · 11. Stress or pressure · 12. Shape · 13. Stability of object's composition · 14. Strength · 15. Duration of action of moving object · 16. Duration of action of stationary object · 17. Temperature · 18. Illumination intensity · 19. Use of energy by moving object · 20. Use of energy by stationary object · 21. Power · 22. Loss of energy · 23. Loss of substance · 24. Loss of information · 25. Loss of time · 26. Quantity of substance / matter · 27. Reliability · 28. Measurement accuracy · 29. Manufacturing precision · 30. External harm affecting the object · 31. Object-generated harmful factors · 32. Ease of manufacture · 33. Ease of operation · 34. Ease of repair · 35. Adaptability or versatility · 36. Device complexity · 37. Difficulty of detecting and measuring · 38. Extent of automation · 39. Productivity.

These cluster naturally into seven groups (used by `assemble_report.py` for the "neighborhood-suggestive principles" section in the no-clean-mapping branch): physical/geometry (1–8), mechanical (9–14), temporal/durability (15–16), energy/thermal (17–22), loss/quantity (23–26), quality/system (27–31), usability/manufacturing (32–39). A matrix may declare its own `meta.parameter_groups` to override.

Always read the matrix's actual parameter description before mapping; a parameter named "Speed" in a software-extended matrix may carry a more specific meaning than the classical mechanical-action sense.

---

## 4. The 40 principles

Brief reference only. **Authoritative descriptions live in each matrix's principles block, including the principle's `interpretation_lineage` and `canonical_id`.** The classical 40 (Altshuller numbering):

1. Segmentation · 2. Taking out / Extraction · 3. Local quality · 4. Asymmetry · 5. Merging / Combining · 6. Universality · 7. Nested doll / Russian dolls · 8. Anti-weight / Counterweight · 9. Preliminary anti-action · 10. Preliminary action · 11. Beforehand cushioning · 12. Equipotentiality · 13. The other way round / Inversion · 14. Spheroidality / Curvature · 15. Dynamics · 16. Partial or excessive action · 17. Another dimension · 18. Mechanical vibration · 19. Periodic action · 20. Continuity of useful action · 21. Skipping / Rushing through · 22. Blessing in disguise / Convert harm to benefit · 23. Feedback · 24. Intermediary · 25. Self-service · 26. Copying · 27. Cheap short-living objects · 28. Mechanics substitution · 29. Pneumatics and hydraulics · 30. Flexible shells and thin films · 31. Porous materials · 32. Color changes · 33. Homogeneity · 34. Discarding and recovering · 35. Parameter changes · 36. Phase transitions · 37. Thermal expansion · 38. Strong oxidants / Boosted interactions · 39. Inert atmosphere · 40. Composite materials.

Each principle has a `canonical_id` (e.g. `P_SEGMENTATION`) that lets the synthesizer dedup across matrices. The matrix file's principle entry also carries the `interpretation_lineage` that determines how the principle should be read (see §8).

---

## 5. Souchkov's empirical finding — when "no clean mapping" is the right answer

Valeri Souchkov, surveying real-world TRIZ practice and education, has reported that only on the order of **10–15% of real industrial problems map cleanly onto the standard 39-parameter contradiction matrix**. The remaining ~85–90% require either reformulation, a different methodology (ARIZ, Substance-Field analysis, the 76 Standard Solutions), or direct expert work without the matrix.

**Implication for this pipeline.** A "no clean mapping" output is a NORMAL output state, not a failure. The pipeline has a dedicated branch for this case (`assemble_report.py --no_resolution`), which produces a report explaining what was tried, the closest considered pairs, and neighborhood-suggestive principles. The mapper and mapping critic are explicitly instructed that honest `mapping_confidence: "low"` and `no_clean_mapping: true` are correct outputs, not last-resort admissions.

This shapes several pipeline behaviours:
- Mapper and critic are instructed not to force a fit.
- The state-driver branches automatically when either declares no-clean-mapping.
- Categorical confidence (high/medium/low) is used everywhere instead of scalar percentages, because Souchkov's finding is itself an empirical-band claim, not a precise number, and pretending finer granularity exists invites false precision.

---

## 6. When the matrix is the wrong tool

Beyond Souchkov's general finding, three specific situations call for non-matrix tools:

**Physical contradictions.** As covered in §2, the matrix has no two-axis structure to apply. Reformulate as an engineering contradiction if a second parameter can be surfaced; otherwise route to ARIZ or the separation principles.

**Problems with no obvious parameter pair.** If the user's contradiction is between values, requirements, or stakeholder interests rather than between measurable parameters (e.g. "we want both privacy and surveillance"), the matrix's parameter set will not capture it. The mapper should set `no_clean_mapping: true`.

**Value-level contradictions.** When the tension is between business outcomes ("conversion rate vs. fraud loss") rather than physical/operational parameters, the user may be better served by service design, regulatory analysis, or product strategy frameworks. The pipeline should still run — sometimes the matrix's principles surprise — but the report should note the framing concern.

In any of these cases, the no-clean-mapping report includes a note: *"This contradiction is not standardly resolved by the matrix; consider reformulation, ARIZ, or a different methodology."*

---

## 7. Cross-domain analogy in BioTRIZ

BioTRIZ is a tradition (Vincent et al., later refined by others) that re-reads the 40 principles through biological mechanisms. The premise is that biology has solved most engineering contradictions at least once over evolutionary time, and the matrix lookups gain explanatory power when the principles are re-presented as analogies to biological mechanisms (cellular compartmentalization, vascular branching, autophagy, allostery, immune-system tolerance, mycelial networks, allometric scaling, etc.).

**Implication for the principle-interpreter.** When working with a matrix declaring `interpretation_lineage: biotriz-40` (currently `biotriz_6x6_bio` and `biotriz_6x6_tech` in this corpus), interpretations MUST draw biological analogies explicitly. A generic "Apply Segmentation to your domain" interpretation for a BioTRIZ matrix erases the value of running BioTRIZ in the first place — the cross-matrix triangulation only works if each matrix's distinct angle is preserved through to the synthesizer.

Concretely, a `biotriz-40` interpretation should:
- Cite a specific biological mechanism (e.g. "like cellular compartmentalization, segregate by access frequency").
- Map the mechanism onto the user's domain (e.g. "hot rules in ribosome-equivalent fast pathways, cold rules in nucleolus-equivalent rare pathways").
- Read as biology-shaped, not as a classical engineering recipe with biology bolted on.

---

## 8. The interpretation_lineage taxonomy

Every matrix in the corpus declares `meta.interpretation_lineage` (and may also declare it per-principle, in which case the per-principle value wins). The lineage tells the principle-interpreter which prompt branch to use.

### `altshuller-40`

Standard application of the classical Altshuller principle. Apply the principle's mechanism to the user's domain in a direct, engineering-shaped way. Most matrices in the canonical and domain status tiers carry this lineage. Examples: `altshuller_39x39`, most domain-curated 39×39 variants.

### `biotriz-40`

The 40 principles re-read as biological analogies (see §7). The interpreter's prompt addendum requires explicit biological mechanism citation. Currently carried by `biotriz_6x6_bio` and `biotriz_6x6_tech`. Generic engineering interpretations under this lineage are a defect.

### `drug-safety-reframed`

The principles have been re-described for governance, regulatory, and safety contexts. The principle entry's description in the matrix file will read as governance-shaped (e.g. "Intermediary" → "Insert an oversight role to break a direct causal link from action to outcome"). The interpreter MUST use the reframed description from the matrix, NOT the classical Altshuller meaning. Carried by drug-safety-related matrices in the corpus. Mistakenly applying the classical Altshuller meaning under this lineage produces interpretations that miss the entire point of the reframing.

### `triz-ai-extended`

The matrix is LLM-curated and extends the classical principles to AI/ML problem spaces. Currently carried by `triz_ai_50x50`. Two implications: (a) the matrix may name principles or parameters that look familiar but have AI-specific meanings (read carefully), and (b) the interpreter MUST emit an `interpretation_caveat: "matrix is LLM-generated; cross-validate against altshuller-40 if available"` field in its output, signalling to the report layer that the suggestion's pedigree is automated curation rather than the classical empirical patent corpus.

These four lineages are the only legal values in the v0.1 vocabulary (enforced by `selector_tags_vocabulary.json` and the interpretation schema enums). Adding a new lineage is a corpus-and-plugin change, not a runtime-extensible field.

---

## 9. Language tag

v0.1 is **English-only**. Matrices declare `meta.language` as a list of BCP 47 tags (e.g. `["en"]`, `["en", "ru"]`, `["ru"]`). `select_matrix.py` Stage A drops any matrix whose `language` does not intersect `["en"]`. There is no `--lang=` flag in v0.1; it is reserved for v1.0+, when bilingual matrix support and non-English subagent prompts ship.

For subagents, this means: assume English input and English output. Do not attempt to translate problems into Russian to "match" a Russian matrix — those matrices will already have been filtered out at Stage A.

---

## 10. ARIZ as an alternative

When the matrix is not the right tool (Souchkov's 85–90%, physical contradictions, value-level tensions), ARIZ — Altshuller's later, longer, more disciplined Algorithm of Inventive Problem Solving — is the canonical TRIZ next step. ARIZ is a structured ~85-step procedure walking from problem statement through ideal final result, contradiction analysis, resource analysis, and standard-solution application, taking hours to days per problem rather than the matrix's minutes.

**v0.1 of this plugin does not implement ARIZ.** The no-clean-mapping report mentions it as a referral. A future plugin (or a sibling skill) might cover ARIZ; the methodology skill should mention it as the conventional escalation.

When framing or interpreting, do not silently fall back to ARIZ-style reasoning — produce a matrix-shaped artifact and let the no-clean-mapping branch handle the referral.

---

## 11. What this skill does NOT cover

- **Specific parameter and principle definitions.** The 39 parameters and 40 principles are listed by name only; authoritative descriptions live in each matrix file's `parameters` and `principles` blocks. Different matrices may give the same-numbered parameter or principle a domain-specific meaning. Always read the matrix file.
- **Matrix metadata and selection routing.** The registry (`registry.json`) is the source of truth for matrix metadata: id, file path, status, language, dimensions, lineage, parameter style. The selection algorithm reads from there; this skill does not duplicate it.
- **Selector-tag vocabulary.** The controlled vocabulary for `selector_tags.*`, `domain_signals`, `exotic_signals`, `domain_classes`, etc. lives in `selector_tags_vocabulary.json` and is governed separately (storage design amendment 2). Do not invent tags from this skill.
- **The state-driver protocol.** What action types `next_action.py` emits, when the orchestrator pauses, how `ask_user` works — all of that is the state-driver's concern. Subagents see only the prompt the orchestrator sends them and produce the artifact named in their system prompt.
- **Cell data.** This skill says nothing about which principles a particular `(improving, worsening)` cell returns. That is a matrix-file lookup performed by `lookup_principles.py`.
- **Schemas.** Each subagent's system prompt names its output schema; the schemas themselves are the authoritative contract. This skill does not duplicate them.
