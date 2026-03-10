# MetaSprint NMA — Design Document
**Date:** 2026-02-27
**Base:** metasprint-dose-response.html (19,308 lines)
**Output:** metasprintnma/metasprint-nma.html

## 1. Overview

Surgical refactor of MetaSprint Dose-Response into a Network Meta-Analysis platform.
~80% reuse (UI, screening, GRADE, RoB, forest/funnel, export, localStorage).
~20% replace (Extract columns, Analysis engine, NMA-specific visualizations).

## 2. Decisions

- **Primary engine:** Frequentist graph-theoretic NMA (Rucker 2012, netmeta-style)
- **Secondary engine:** Bayesian NMA (Lu & Ades, MH-MCMC in JS) — toggle
- **Domain:** Cardiovascular (CardioRCT screening, drug class subcategories)
- **Component NMA:** Papakonstantinou et al. (2018) contribution matrix
- **localStorage prefix:** `metaSprintNMA_` (unique from dose-response)

## 3. Extract Phase Changes

### Remove
- Dose, Unit, Ref Dose columns
- One-stage / Two-stage radio toggle
- Dose-response validation

### Add
- **Treatment 1** (dropdown/text — the intervention arm)
- **Treatment 2** (dropdown/text — the comparator arm)
- **Multi-arm detection:** Same Study ID with >2 unique treatments = multi-arm trial
  - Auto-generate all pairwise comparisons
  - Adjust variance-covariance for shared arms

### Keep
- Study ID, Trial ID, NCT, PMID, DOI, Outcome, N, Effect, Lower CI, Upper CI, SE, Type, Subgroup, Notes, RoB

### Columns (final order)
Study ID | Trial ID | NCT | PMID | DOI | Outcome | Treatment 1 | Treatment 2 | N1 | N2 | Effect | Lower CI | Upper CI | SE | Type | Subgroup | Notes

## 4. Analysis Engine

### 4A. Frequentist NMA (default)

**Graph-theoretic approach (Rucker 2012):**
1. Build edge list from pairwise comparisons
2. Construct **B** matrix (design/incidence matrix): rows=comparisons, cols=treatments
3. Choose reference treatment (most connected or user-selected)
4. Weight matrix **W** = diag(1/variance) for each comparison
5. Laplacian **L** = B^T W B
6. Network estimates: solve L * d = B^T W y (where y = observed effects, d = treatment effects vs reference)
7. Variance-covariance of d from L^{-1} (Moore-Penrose pseudoinverse)

**Heterogeneity:**
- Common tau^2 across network (DL method of moments)
- Q_total, Q_heterogeneity, Q_inconsistency decomposition
- I^2 per comparison and global

**P-scores (Rucker & Schwarzer 2015):**
- For each treatment pair (i,j): P(treatment i better than j) = Phi((d_i - d_j) / sqrt(var_i + var_j - 2*cov_ij))
- P-score_i = mean of P(i better than j) for all j != i
- Range [0,1], higher = better

**Bucher indirect comparison:**
- For triangular loop A-B, A-C: indirect B-C = d_AC - d_AB
- SE_indirect = sqrt(SE_AB^2 + SE_AC^2)
- Used in node-splitting for consistency check

### 4B. Bayesian NMA (toggle)

**Model (Lu & Ades 2004):**
- y_ijk ~ N(d_jk, sigma^2_ijk)  [observed effect for study i, comparison j vs k]
- d_jk = mu_j - mu_k  (consistency)
- mu_j ~ N(0, 100)  [vague prior on treatment effects]
- tau ~ HalfNormal(0, 1)  [between-study SD]

**MCMC:**
- Metropolis-Hastings with adaptive step size
- 4 chains, 5000 warmup + 10000 samples each
- Gelman-Rubin R-hat convergence diagnostic
- Effective sample size (ESS)

**Outputs:**
- Posterior median + 95% CrI for each d_jk
- SUCRA = (mean rank - 1) / (n_treatments - 1) from posterior rank samples
- Rank probability matrix
- DIC (Deviance Information Criterion)

### 4C. Component NMA (Papakonstantinou 2018)

**Contribution matrix:**
- For each network estimate d_jk, compute % contribution from each direct comparison
- Based on hat matrix H = B(B^T W B)^{-1} B^T W
- Rows of H show how each pairwise comparison contributes to pooled estimates
- Visualize as stacked bar chart or heatmap

**Random-effects extension:**
- Use adjusted weights W* = diag(1/(variance + tau^2))
- Recompute hat matrix with W*

## 5. Consistency Testing

### Node-splitting (Dias 2010)
- For each comparison with both direct and indirect evidence:
  - Estimate direct effect (from studies directly comparing A vs B)
  - Estimate indirect effect (from network excluding direct A-B studies)
  - Test: z = (direct - indirect) / sqrt(SE_direct^2 + SE_indirect^2)
  - p-value < 0.05 flags inconsistency

### Global inconsistency
- Q_inconsistency = Q_total - Q_heterogeneity
- df_inconsistency = number of independent loops
- chi-square test

### Design-by-treatment interaction (Higgins 2012)
- Alternative global test
- More powerful when inconsistency is spread across designs

## 6. New Visualizations

### Network Plot (SVG, force-directed)
- Nodes = treatments (size proportional to total N or study count)
- Edges = direct comparisons (width proportional to inverse variance or study count)
- Color = treatment class (SGLT2=blue, ACEi=green, etc.)
- Interactive: drag nodes, hover for details
- Disconnected components shown with warning

### League Table (HTML table)
- Upper triangle: effect estimate (95% CI) — row treatment vs column treatment
- Lower triangle: mirror (inverse effect)
- Diagonal: treatment name
- Color coding: green=significant favoring row, red=significant favoring column, grey=non-significant
- Sortable by P-score

### Rank Probability Heatmap (Canvas)
- Rows = treatments, Cols = ranks (1st, 2nd, ..., last)
- Cell color = probability (white=0, dark blue=1)
- Shows full ranking uncertainty

### P-score / SUCRA Bars (SVG)
- Horizontal bar chart
- Frequentist: P-scores
- Bayesian: SUCRA values
- Sorted descending

### Comparison-Adjusted Funnel (Canvas)
- X-axis: comparison-specific residual
- Y-axis: 1/SE (inverted)
- Centered at 0 if no asymmetry
- Chaimani et al. (2013) approach

### Consistency Forest (SVG)
- For each node-split comparison:
  - Direct estimate (diamond)
  - Indirect estimate (square)
  - Network estimate (combined)
  - p-value for inconsistency

### Contribution Heatmap (Canvas)
- Rows = network estimates (A vs B, A vs C, etc.)
- Cols = direct comparisons
- Cell = % contribution (color intensity)

## 7. GRADE-NMA Extensions

Starting from standard GRADE (already implemented), add NMA-specific domains:

### Intransitivity
- Check: are study populations / designs similar across comparisons?
- Auto-flag if treatment classes span very different populations
- Downgrade -1 if concerning

### Incoherence (Inconsistency)
- Check: node-splitting p-values + global inconsistency test
- Downgrade -1 if any node-split p<0.05 or global Q_inconsistency significant

### Indirectness (enhanced)
- For comparisons with only indirect evidence: automatic -1 downgrade
- For mixed: weight by % direct contribution (from component NMA)

## 8. Reused Components (no changes)

- Dashboard (40-day sprint, health score, DoD gates)
- Discover (universe, 7 visualization views — network graph already exists!)
- Protocol (PICO, PROSPERO template)
- Search (6 sources: PubMed, OpenAlex, CT.gov, AACT, EuropePMC, CrossRef)
- Screen (CardioRCT engine, auto-screener, dedup, PRISMA)
- Checkpoints (DoD tracking)
- Write (auto-generate Methods/Results — updated templates)
- 15 Insights sub-tabs (adapted labels where needed)
- Dark/light mode, undo/redo, accessibility
- Forest plot core (per-comparison), funnel plot core
- RoB 2 assessment
- NNT/NNH calculation (per comparison)
- Export (CSV/JSON/SVG)

## 9. Renaming

| From | To |
|------|-----|
| MetaSprint Dose-Response | MetaSprint NMA |
| Dose-Response Meta-Analysis Platform | Network Meta-Analysis Platform |
| Dose, Unit, Ref Dose | Treatment 1, Treatment 2 |
| DR Model (Linear/Quadratic/Emax) | NMA Model (Consistency/Inconsistency) |
| Effect per unit dose | Relative treatment effect |
| metaSprint_project_ | metaSprintNMA_project_ |
| dose-response.csv | nma-comparisons.csv |

## 10. File Output

Single file: `metasprint-nma.html` in `C:\Users\user\Downloads\metasprintnma\`
