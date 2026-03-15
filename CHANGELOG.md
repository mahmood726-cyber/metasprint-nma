# Changelog

## [1.0.0] - 2026-03-15

### Added
- 70 pre-loaded clinical NMA topics across 10 therapeutic areas (oncology, cardiology, neurology, rheumatology, infectious disease, gastroenterology, respiratory, bone/metabolic, hematology, teaching)
- WebR in-browser R validation (netmeta via WebAssembly)
- Downloadable R validation script with tolerance-based PASS/FAIL assertions
- Gold standard regression testing (smoking, CKD, minimal datasets)
- Multi-tier concordance matching (T1-T4, adapted from RCT Extractor v2)
- Treatment rank clustering (Papakonstantinou 2022, silhouette-optimal k-means)
- Net heat plot (Krahn 2013, H[i,j] * residual[j] inconsistency decomposition)
- Threshold analysis (Caldwell 2016, ranking robustness assessment)
- Tool comparison table (23 features x 5 tools)
- Reviewer Evidence Packet (one-click export: analysis + validation + PRISMA)
- PRISMA-NMA interactive checklist (Hutton 2015, 32 items, localStorage-persisted)
- PICO color-coded abstract highlighting (Population blue, Intervention green, Comparator orange, Outcome purple)
- Demographic extraction from CT.gov baseline characteristics (age, sex, eligibility)
- 2x2 event data extraction with Woolf log-OR computation
- Enhanced abstract parser (SMD, IRR, NEJM/bracket styles, negative context filter)
- Auto-normalization of treatment names using topic normMaps after extraction
- Self-contained demo loading (all 70 topics runnable offline from published reference data)
- Auto-save to localStorage (30-second interval + beforeunload)
- Guided tutorial walkthrough (4 steps, keyboard-navigable)
- Top progress bar during NMA analysis
- Keyboard shortcuts (Ctrl+Enter run, Ctrl+S save, Ctrl+Z/Y undo/redo)
- sanitizeForR() function for R code injection prevention
- 97 Selenium tests (test_session_features.py + test_expanded_suite.py)
- F1000Research manuscript

### Security
- CSP hardened for WebR (webr.r-wasm.org, repo.r-wasm.org, worker-src)
- sanitizeForR() applied to all R code generation paths
- escapeHtml() verified on all user-facing treatment names in HTML/SVG
- 4 rounds of 5-persona multi-persona review (18 issues found, all fixed)

### Accessibility
- Skip link, ARIA landmarks, aria-live regions
- Focus trapping in modals, keyboard navigation for tutorial
- Color-blind safe verdict icons ([=]/[~]/[x]) and cluster palette
- WCAG AA contrast on grade badges
- prefers-reduced-motion support
