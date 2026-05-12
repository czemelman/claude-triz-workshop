# TRIZ Contradiction Matrix Meta-Analysis

Generated: 2026-03-25

## 1. Side-by-Side Matrix Comparison

| Property | altshuller_39x39 | russian_original | matriz_org_39x39 | heinrich_39x39 | biotriz_6x6 (tech) | biotriz_6x6 (bio) | mann_48x48 |
|---|---|---|---|---|---|---|---|
| **Dimensions** | 39x39 | 39x39 | 39x39 | 39x39 | 6x6 | 6x6 | 48x48 |
| **Domain** | General engineering | General engineering | General engineering | General engineering (curated) | Technology problem solving | Biology problem solving | General engineering (updated) |
| **Year** | 1971 | 1971 | 1971 | 2023 | 2006 | 2006 | 2003 |
| **Populated cells** | 1244 | 1244 | 1244 | 109 | 36 | 36 | 0 |
| **Possible cells** | 1482 | 1482 | 1482 | 1482 | 30* | 30* | 2256 |
| **Sparsity** | 16.1% | 16.1% | 16.1% | 92.7% | -20.0%* | -20.0%* | 100% |
| **Principles defined** | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| **Principles referenced** | 40 | 40 | 40 | 30 | 40 | 36 | 0 |
| **Avg principles/cell** | 3.37 | 3.37 | 3.37 | 3.07 | 4.00 | 5.28 | N/A |
| **Max principles/cell** | 4 | 4 | 4 | 4 | 9 | 9 | N/A |
| **Most referenced** | P35 (415) | P35 (415) | P35 (415) | P15 (78) | P19 (9) | P3 (25) | N/A |
| **Diagonal cells** | No | No | No | No | Yes (6) | Yes (6) | N/A |

*BioTRIZ includes diagonal cells (same-field contradictions), so populated cells exceed off-diagonal count. Sparsity computed against off-diagonal cells only.

---

## 2. Principle Frequency Analysis (All Matrices Combined)

Frequency counts across altshuller_39x39, biotriz_6x6 (both sub-matrices), and heinrich_39x39. The russian_original and matriz_org are excluded as they are identical copies of the altshuller matrix.

### 2.1 Full Frequency Table

| Rank | Principle | Name | Total References |
|---|---|---|---|
| 1 | P35 | Parameter changes | 492 |
| 2 | P10 | Preliminary action | 282 |
| 3 | P1 | Segmentation | 281 |
| 4 | P15 | Dynamics | 261 |
| 5 | P28 | Mechanics substitution | 240 |
| 6 | P2 | Taking out | 234 |
| 7 | P18 | Mechanical vibration | 186 |
| 8 | P19 | Periodic action | 180 |
| 9 | P3 | Local quality | 161 |
| 10 | P13 | The other way round | 157 |
| 11 | P32 | Color changes | 151 |
| 12 | P26 | Copying | 146 |
| 13 | P27 | Cheap short-living objects | 129 |
| 14 | P29 | Pneumatics and hydraulics | 122 |
| 15 | P34 | Discarding and recovering | 110 |
| 16 | P14 | Spheroidality | 109 |
| 17 | P22 | Blessing in disguise | 106 |
| 18 | P16 | Partial or excessive actions | 103 |
| 19 | P40 | Composite materials | 102 |
| 20 | P24 | Intermediary | 101 |
| 21 | P17 | Another dimension | 98 |
| 22 | P6 | Universality | 95 |
| 23 | P4 | Asymmetry | 95 |
| 24 | P36 | Phase transitions | 84 |
| 25 | P8 | Anti-weight | 83 |
| 26 | P39 | Inert atmosphere | 79 |
| 27 | P30 | Flexible shells and thin films | 77 |
| 28 | P37 | Thermal expansion | 68 |
| 29 | P25 | Self-service | 66 |
| 30 | P38 | Strong oxidants | 56 |
| 31 | P31 | Porous materials | 56 |
| 32 | P11 | Beforehand cushioning | 53 |
| 33 | P7 | Nested doll | 43 |
| 34 | P5 | Merging | 42 |
| 35 | P23 | Feedback | 42 |
| 36 | P21 | Skipping | 39 |
| 37 | P12 | Equipotentiality | 36 |
| 38 | P33 | Homogeneity | 34 |
| 39 | P9 | Preliminary anti-action | 33 |
| 40 | P20 | Continuity of useful action | 25 |

### 2.2 Distribution Shape

The distribution follows a power-law pattern. P35 (Parameter changes) alone accounts for 492 references, nearly 2x the second-most-frequent principle. The top 10 principles account for approximately 65% of all references, while the bottom 10 account for less than 10%.

---

## 3. Universal vs. Domain-Specific Principles

### 3.1 Principles Present in Every Matrix

30 of 40 principles appear in all three distinct matrices (altshuller, biotriz, heinrich):

P1 (Segmentation), P2 (Taking out), P3 (Local quality), P4 (Asymmetry), P7 (Nested doll), P8 (Anti-weight), P11 (Beforehand cushioning), P13 (The other way round), P14 (Spheroidality), P15 (Dynamics), P16 (Partial or excessive actions), P17 (Another dimension), P18 (Mechanical vibration), P19 (Periodic action), P22 (Blessing in disguise), P23 (Feedback), P25 (Self-service), P28 (Mechanics substitution), P29 (Pneumatics and hydraulics), P30 (Flexible shells and thin films), P31 (Porous materials), P32 (Color changes), P33 (Homogeneity), P34 (Discarding and recovering), P35 (Parameter changes), P36 (Phase transitions), P37 (Thermal expansion), P38 (Strong oxidants), P39 (Inert atmosphere), P40 (Composite materials)

### 3.2 Principles Missing from Specific Matrices

**Absent from Heinrich (10 principles):**
P5 (Merging), P6 (Universality), P9 (Preliminary anti-action), P10 (Preliminary action), P12 (Equipotentiality), P20 (Continuity of useful action), P21 (Skipping), P24 (Intermediary), P26 (Copying), P27 (Cheap short-living objects)

These absences are notable because Heinrich is a curated subset. The missing principles are not uniformly "rare" in the classic matrix -- P10 (Preliminary action) is the 2nd most frequent principle in the classic matrix, and P26 (Copying) is the 12th most frequent. This confirms Heinrich applies a different selection methodology.

**Absent from BioTRIZ biology matrix (4 principles):**
P8 (Anti-weight), P12 (Equipotentiality), P28 (Mechanics substitution), P39 (Inert atmosphere)

These absences make biological sense: anti-weight, equipotentiality, mechanics substitution, and inert atmosphere are engineering-centric concepts that have no natural analogue in biological systems.

### 3.3 Domain-Specific Emphasis

| Principle | Classic (altshuller) | BioTRIZ Tech | BioTRIZ Bio | Heinrich |
|---|---|---|---|---|
| P3 (Local quality) | Rank 12 | Rank 14 | **Rank 1** (25 cells) | Rank 14 |
| P35 (Parameter changes) | **Rank 1** | Rank 5 | Rank 12 | **Rank 2** |
| P15 (Dynamics) | Rank 7 | **Rank 2** | **Rank 3** | **Rank 1** |
| P19 (Periodic action) | Rank 8 | **Rank 1** (9 cells) | Rank 7 | Rank 13 |
| P25 (Self-service) | Rank 29 | Rank 7 | **Rank 4** (14 cells) | Rank 17 |

Key insight: Biology heavily favors P3 (Local quality) -- the principle of making structures non-uniform and functionally differentiated. This aligns with how biological systems achieve complexity through cell differentiation and tissue specialization rather than through the parameter changes and mechanical substitutions favored by engineering.

---

## 4. Cross-Source Consensus for 39x39 Matrices

### 4.1 Perfect Consensus Cells

Among cells present in 2 or more sources:
- **1157 cells** have perfect agreement across all sources that contain them
- **87 cells** show disagreement (all involving Heinrich vs. the classic three)
- **Agreement rate: 93.0%**

The three canonical sources (triz40.com, altshuller.ru, MATRIZ.org) agree on 100% of their 1244 shared cells. The entire disagreement comes from the Heinrich derivative.

### 4.2 Heinrich Overlap Analysis

Of the 109 Heinrich cells:
- **87 cells** overlap with the classic matrix (all disagree on exact principle lists)
- **22 cells** are unique to Heinrich (not present in classic)
- **0 cells** have an exact match with the classic matrix
- **46 cells** have partial overlap (at least one principle in common)
- **41 cells** have zero overlap (completely different principles)

### 4.3 Most Consensual Parameter Pairs

The strongest consensus exists in cells where all four sources agree. These are the 1157 cells from the classic matrix that Heinrich does not cover. Among the cells that Heinrich does cover, none achieve full consensus, making these the most contested parameter pairs. The rows most heavily represented in discrepancies are:
- **Row 14 (Strength)**: 28 disagreement cells (Heinrich covers strength extensively with its own principle assignments)
- **Row 19 (Use of energy by moving object)**: 18 disagreement cells
- **Row 9 (Speed)**: 8 disagreement cells

---

## 5. How Domain-Specific Matrices Modify the Classic

### 5.1 BioTRIZ Modifications

The BioTRIZ matrices are not subsets or modifications of the classic 39x39 matrix. They use an entirely different parameter framework (6 operational fields vs. 39 engineering parameters). However, they reuse the same 40 inventive principles, enabling comparison at the principle level.

**Key structural differences:**
- BioTRIZ includes diagonal cells (same-field contradictions), which the classic matrix does not
- BioTRIZ biology matrix averages 5.28 principles per cell vs. 3.37 in the classic, suggesting biological solutions tend to be more multi-faceted
- The technology sub-matrix averages 4.00 principles per cell, falling between the classic and biology values
- The maximum of 9 principles per cell (BioTRIZ) far exceeds the classic maximum of 4

**Principle redistribution:**
- The biology matrix's dominant principle P3 (Local quality, 25 cells = 69% of cells) has no equivalent dominance in the classic matrix (P3 ranks only 12th)
- P25 (Self-service) rises from rank 29 in the classic to rank 4 in biology, reflecting how biological systems inherently serve themselves
- P19 (Periodic action) is the top principle in the technology sub-matrix (9 cells) but only 8th in the classic, suggesting the 6x6 framework emphasizes cyclical processes

**The 12% similarity finding:** The original paper reports only 12% overall similarity between technology and biology solutions for the same contradictions. This quantifies how fundamentally different biological and engineering problem-solving strategies are, even when mapped to the same principle vocabulary.

### 5.2 Heinrich as a Modified Classic

Heinrich is nominally a 39x39 matrix using the same parameters and principles, but functionally it is a heavily curated derivative:
- Only 7.4% of possible cells are populated (109 vs. 1482)
- Principle P15 (Dynamics) appears in 71.6% of all Heinrich cells, compared to its natural frequency of ~12% in the classic matrix
- Principle P35 (Parameter changes) appears in 64.2% of Heinrich cells (vs. ~33% in classic)
- This extreme concentration suggests Heinrich's AI system uses a small set of "universal" principles as defaults rather than the cell-specific recommendations of the classic matrix

---

## 6. Universal Core Subset Assessment

### 6.1 Can a Subset of Principles Cover 80%+ of Cells?

**In the classic Altshuller matrix:**
- The top **22 principles** (55% of all 40) cover 80.2% of all principle references
- The top **10 principles** cover 50.8% of references
- No single principle exceeds 10% of total references

The 22 principles needed for 80% coverage are:
P35 (Parameter changes), P10 (Preliminary action), P1 (Segmentation), P28 (Mechanics substitution), P2 (Taking out), P18 (Mechanical vibration), P15 (Dynamics), P19 (Periodic action), P32 (Color changes), P13 (The other way round), P26 (Copying), P3 (Local quality), P27 (Cheap short-living objects), P29 (Pneumatics and hydraulics), P34 (Discarding and recovering), P16 (Partial or excessive actions), P40 (Composite materials), P24 (Intermediary), P17 (Another dimension), P6 (Universality), P22 (Blessing in disguise), P14 (Spheroidality)

**Across all matrices combined:**
The same top-heavy distribution holds. However, the specific ranking shifts by domain:
- Engineering (classic): P35 dominates
- Biology (BioTRIZ bio): P3 dominates
- Curated AI (Heinrich): P15 dominates

**Assessment:** There is no compact "universal core" of fewer than ~20 principles that covers 80% of all usage. The 40-principle system is well-utilized, with the bottom 18 principles still accounting for 20% of references. However, a practitioner familiar with the top 10 principles (P35, P10, P1, P28, P2, P18, P15, P19, P3, P13) would have coverage of approximately half of all matrix recommendations, making these a reasonable "starter set."

### 6.2 Cross-Domain Stability

Principles that rank in the top 10 across multiple distinct matrices represent the most universally applicable concepts:

| Principle | Classic Rank | BioTRIZ Tech Rank | BioTRIZ Bio Rank | Universal? |
|---|---|---|---|---|
| P35 (Parameter changes) | 1 | 5 | 12 | Moderate |
| P15 (Dynamics) | 7 | 2 | 3 | **Strong** |
| P1 (Segmentation) | 3 | 12 | 2 | **Strong** |
| P3 (Local quality) | 12 | 14 | 1 | Moderate |
| P19 (Periodic action) | 8 | 1 | 7 | **Strong** |
| P22 (Blessing in disguise) | 17 | 3 | 6 | Moderate |

**P15 (Dynamics)** and **P1 (Segmentation)** emerge as the most universally applicable principles -- they rank highly in engineering, biology, and the curated Heinrich system. **P19 (Periodic action)** is also consistently high-ranking.

---

## 7. Parameter Mapping Across Domains

### 7.1 Classic 39 to Mann 48

Mann's 2003 updated matrix reorganized the classic 39 parameters into 48, with these notable changes:

| Classic Parameter | Mann Equivalent | Change |
|---|---|---|
| Force (Intensity) #10 | Force/Torque #15 | Renamed, torque added |
| Shape #12 | Shape #9 | Renumbered |
| Stress or pressure #11 | Stress/Pressure #19 | Renumbered |
| Loss of Energy #22 | Loss of Energy #27 | Renumbered |
| Ease of operation #33 | Trainability/Operability/Controllability #34 | Expanded |
| Ease of repair #34 | Repairability #36 | Renamed |
| Adaptability #35 | Adaptability/Versatility #32 | Renumbered |
| Device complexity #36 | System Complexity #44 + Control Complexity #45 | Split |
| Difficulty of detecting #37 | Ability to Detect/Measure #46 + Measurement Precision #47 | Split |
| (new) | Amount of Substance #10 | Added |
| (new) | Amount of Information #11 | Added |
| (new) | Function Efficiency #24 | Added |
| (new) | Noise #29 | Added |
| (new) | Harmful Emissions #30 | Added |
| (new) | Compatibility/Connectivity #33 | Added |
| (new) | Security/Safety/Vulnerability #37 | Added |
| (new) | Aesthetics/Appearance #38 | Added |
| (new) | Other Harmful Effects Acting on System #39 | Added |

Mann retained the moving/stationary object dichotomy for physical parameters (weight, length, area, volume, duration, energy) while adding parameters for information, safety, aesthetics, and noise that reflect modern engineering concerns.

### 7.2 Classic 39 to BioTRIZ 6

The BioTRIZ parameters are abstractions that each encompass multiple classic parameters:

| BioTRIZ Parameter | Classic Parameters Mapped |
|---|---|
| Substance | Weight (#1-2), Quantity of substance (#26), Loss of substance (#23) |
| Structure | Shape (#12), Stability (#13), Strength (#14), Device complexity (#36) |
| Space | Length (#3-4), Area (#5-6), Volume (#7-8) |
| Time | Duration of action (#15-16), Loss of Time (#25), Speed (#9) |
| Energy | Power (#21), Use of energy (#19-20), Loss of Energy (#22), Temperature (#17) |
| Information | Illumination (#18), Loss of Information (#24), Measurement accuracy (#28), Detecting/measuring (#37) |

This 6-parameter framework deliberately collapses the 39 engineering-specific parameters into fundamental physical categories, enabling cross-domain comparison between technology and biology.

---

## 8. Summary of Findings

1. **Data integrity is high.** The three canonical sources for the classic Altshuller matrix (triz40.com, altshuller.ru, MATRIZ.org) are perfectly identical. All spot-checks against original sources passed with 100% accuracy.

2. **Heinrich is a derivative, not an alternative.** Its 109 cells use systematically different principle assignments from the classic matrix, with zero exact matches on shared cells and heavy concentration on P15 (Dynamics) and P35 (Parameter changes).

3. **No compact universal core exists.** 22 of 40 principles are needed to cover 80% of classic matrix references. All 40 principles serve a purpose.

4. **Domain adaptation changes principle priorities.** Biology emphasizes P3 (Local quality) and P25 (Self-service); technology emphasizes P35 (Parameter changes) and P10 (Preliminary action). Only P15 (Dynamics) and P1 (Segmentation) rank consistently high across all domains.

5. **BioTRIZ reveals fundamental strategy differences.** With only 12% overlap between technology and biology solutions, the matrices quantify how differently nature and engineering solve the same categories of contradictions.

6. **Mann's 48-parameter extension modernizes but needs data.** The 9 new parameters (noise, safety, aesthetics, information quantity, etc.) address genuine gaps in the classic matrix but the matrix cell data could not be extracted from the available PDF source.
