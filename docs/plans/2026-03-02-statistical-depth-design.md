# MetaSprint NMA — Statistical Depth Enhancement Design

**Date:** 2026-03-02
**Goal:** Add 4 advanced NMA methods inline in the Analyze tab

## 1. Contribution Matrix (Papakonstantinou 2018)

**Computation:** `H = B(B'WB)⁻¹B'W` — hat matrix showing how much each direct comparison contributes to each network estimate.
- Input: design matrix `B` (nT×nE), weight matrix `W` (diagonal, nE×nE) — already computed in `runFrequentistNMA()`
- Output: `H` matrix (nE×nE), row sums = 1.0, values 0–1
- Container: `<div id="contributionMatrixContainer">` after consistency forest

**Visualization:**
- Heatmap table: rows = network estimates, columns = direct comparisons, cell color = contribution weight
- Stream/alluvial plot: evidence flow from direct comparisons into network estimates

**Export:** CSV of raw H matrix values.

## 2. CINeMA Framework (Nikolakopoulou 2020)

**Six domains per network comparison:**
1. Within-study bias — RoB weighted by contribution matrix flow
2. Across-study bias — Egger/Peters p + Copas + S-value
3. Indirectness — proportion of indirect evidence (from contribution matrix)
4. Imprecision — CI width vs clinical decision threshold (user-configurable)
5. Heterogeneity — prediction interval includes null/clinical threshold
6. Incoherence — node-splitting p-value (already computed)

**Rating:** Each domain → No concerns / Some concerns / Major concerns.
Overall → High / Moderate / Low / Very Low confidence.

**Visualization:** Color-coded table (green/yellow/red) per comparison × domain.
**Dependency:** Requires contribution matrix for domains 1 and 3.

## 3. PET-PEESE + Harbord Test

**PET-PEESE (Stanley & Doucouliagos 2014):**
- PET: WLS regression yi ~ sei, weights=1/sei². If intercept p < 0.05, use PEESE (yi ~ sei²).
- Display: corrected estimate + funnel plot overlay line.

**Harbord test (Harbord 2006):**
- Score-based asymmetry test for binary outcomes (OR).
- Z/√V vs 1/√V regression.
- More appropriate than Egger for log-OR.

**Where:** Extended `eggerContainer` section.

## 4. Component NMA (Rücker 2020)

**MVP — additive model only:**
- Parse treatment names into components (separator: `+`)
- Build component design matrix C (nE × nComponents)
- Solve: β = (C'WC)⁻¹C'Wy for component effects
- Display: forest plot of individual component effects

**UI:** Component separator input + "Detect Components" button.
**Container:** `<div id="componentNMAContainer">`

## Implementation Order

1. Contribution Matrix + Stream Plot (foundation)
2. CINeMA Framework (depends on #1)
3. PET-PEESE + Harbord (independent, quick)
4. Component NMA (most complex, independent)

## Layout

All render inline in the Analyze tab as additional auto-generated sections below existing results.
