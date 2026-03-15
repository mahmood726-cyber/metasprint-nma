# MetaSprint NMA — Validation Summary

## Overview
MetaSprint NMA implements three independent validation mechanisms to enable reviewer verification of computational accuracy without requiring R installation.

## Mechanism 1: WebR In-Browser Validation
- Loads the R runtime (~20MB) via WebAssembly (webr.r-wasm.org v0.4.4)
- Installs and runs the `netmeta` R package directly in the browser
- Compares tau-squared, I-squared, Q-statistic, treatment effects (d[]), and P-scores
- Displays tolerance-based PASS/FAIL table with per-metric comparison
- All computation runs locally; no data leaves the browser

## Mechanism 2: Downloadable R Validation Script
- Generates a complete R script containing:
  - Study data in `data.frame()` format
  - `netmeta()` call matching app settings (tau-squared method, confidence level, reference treatment)
  - App's computed values as R variables
  - `check()` function with tolerance-based PASS/FAIL assertions
  - Summary verdict (X/Y PASSED)
  - Forest plot, network graph, and ranking for visual confirmation
- Uses `sanitizeForR()` to prevent R code injection from treatment names
- Reviewer can run in R (>= 4.1) with netmeta installed

## Mechanism 3: Gold Standard Regression Testing
- Three canonical datasets with pre-computed reference values:
  - **Smoking cessation** (Hasselblad 1998): 24 contrasts, 4 treatments, DL tau-squared
  - **CKD nephroprotection**: 5 trials (CREDENCE, DAPA-CKD, EMPA-KIDNEY, FIDELIO, FIGARO), star network
  - **Minimal**: 3 pairwise studies, analytical inverse-variance reference
- Runs automatically on every NMA analysis
- Displays pass/fail badge in the published comparison container
- Tolerances: tau-squared +/-0.001, effects +/-0.005, P-scores +/-0.02, I-squared +/-2%

## Automated Test Suite
- **test_session_features.py**: 49 Selenium tests (concordance, WebR UI, keyboard shortcuts, auto-save, tutorial, net heat, clustering, progress bar, CSP, accessibility)
- **test_expanded_suite.py**: 48 Selenium tests (threshold analysis, tool comparison, reviewer packet, PRISMA checklist, gold standard validation, matchTier, batch topic validation, sanitizeForR)
- **test_nma_comprehensive.py**: 410+ assertions (NMA engine, LOO, Baujat, exports)
- **Total: 500+ automated tests**

## Concordance with Published References
- 23 clinical reference datasets spanning oncology (16), cardiology/nephrology (4), hematology (2), teaching (1)
- Multi-tier matching (T1-T4, adapted from RCT Extractor v2):
  - T1: exact match within 5%
  - T2: reciprocal (1/HR) or sign-flip (-MD) within 5%
  - T3: close match within 10%
  - T4: approximate match within 20%
- Bidirectional CI overlap + Jaccard CI overlap + Spearman rank correlation

## Security Review
- Two rounds of 5-persona multi-persona review (44 issues found, all fixed)
- `sanitizeForR()` applied to all R code generation paths
- `escapeHtml()` on all user-facing treatment names in HTML/SVG
- CSP with WebR domains, worker-src for WebAssembly
- No eval(), no prototype pollution, no ReDoS patterns
