# MetaSprint NMA v2 Improvement Sprint

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 6 critical bugs, add 12 statistical/visualization improvements, 10 UX/export fixes, and 8 security hardening items across the MetaSprint NMA single-file app.

**Architecture:** Single-file HTML app (22,747 lines). All edits target `metasprint-nma.html`. Tests in `test_nma_comprehensive.py` (Selenium, 211/211 passing). No build system — direct HTML edits.

**Tech Stack:** Vanilla JS, SVG charts, IndexedDB, Selenium/Python tests

---

## Phase A: Critical Bugs (6 tasks)

### Task A1: Fix hardcoded z=1.96 in compute2x2Effect

**Files:** Modify `metasprint-nma.html:6679`

Line 6679: `var z = 1.96;` ignores user-selected confidence level. The function has no `confLevel` parameter.

**Fix:** Add `confLevel` parameter, use `normalQuantile(1 - (1-confLevel)/2)`. Update all callers to pass confLevel.

### Task A2: Replace Math.random() with seeded PRNG in P-score MC

**Files:** Modify `metasprint-nma.html:10847`

Line 10847: `const u1 = Math.random(), u2 = Math.random()` in `computeFrequentistRankProbs`. Non-deterministic.

**Fix:** Create a local seeded RNG instance (mulberry32 or use existing xoshiro128ss) with fixed seed, pass to the MC loop.

### Task A3: Fix Bayesian MCMC reference treatment

**Files:** Modify `metasprint-nma.html:10100`

Line 10100: `const refIdx = 0;` always uses treatment index 0. Should use user-selected reference.

**Fix:** Read reference from `nmaRefSelect` DOM element (same as frequentist engine at line 9880), or accept refIdx as parameter.

### Task A4: Fix disconnected network filter using canonical names

**Files:** Modify `metasprint-nma.html:11546-11549`

Lines 11546-11549: `keepTreatSet` contains canonical names but `s.treatment1?.trim()` is raw input. Mismatch after normalization.

**Fix:** Apply `normalizeTreatmentName()` to treatment names before checking `keepTreatSet.has()`.

### Task A5: Guard forest plot tick loop against infinite loop

**Files:** Modify `metasprint-nma.html:11113,11267`

Lines 11113 and 11267: When `range <= 0`, `step = 0` → infinite loop.

**Fix:** Add `if (range < 1e-10) range = 1;` guard before both tick loops.

### Task A6: Fix dark mode light-forced toggle

**Files:** Modify `metasprint-nma.html:3306-3319`

Line 3306: `toggleDarkMode` should add `light-forced` when user turns off dark mode while system is dark. Current logic already does this (lines 3310-3313) — verified correct. BUT on page load, the stored preference `metaSprintNMA_dark === '0'` is not checked against system dark. Fix the init path.

---

## Phase B: Statistical & Visualization Polish (12 tasks)

### Task B1: Forest plot heterogeneity footer

Add I2, tau2, Q, p stats below the x-axis in both `renderForestPlot` (before line 11129) and `renderNMAForestPlot` (before line 11291).

### Task B2: Funnel plot x-axis ticks + multi-contour

Add x-axis tick marks/labels and p=0.10/0.05/0.01 significance contour regions to `renderFunnelPlot` (lines 11312-11334).

### Task B3: League table colorblind-safe indicators

Replace red/green-only cell coloring (line 10703) with symbols (arrows/icons) + accessible colors. Add upward/downward arrow indicators.

### Task B4: P-score direction toggle

Add UI toggle for "lower is better" / "higher is better" near the reference treatment select. Wire to `pscoreSign` (line 9999).

### Task B5: Hedges J exact formula for small df

Line 6735: Replace approximation with exact gamma formula when df <= 2.

### Task B6: Node-split t-distribution

Line 10349: Use t-distribution with appropriate df instead of z for node-split p-values.

### Task B7: pD < 0 DIC warning

Lines 10270-10271: Add warning when pD is negative.

### Task B8: Trim-and-fill on funnel plot

Add imputed studies as hollow circles on the funnel plot SVG.

### Task B9: Network plot viewBox + edge labels

Line 10543: Add viewBox attribute. Add numeric study count labels on edges.

### Task B10: Rank heatmap diverging palette

Lines 10790-10793: Replace single blue opacity ramp with a diverging YlGnBu palette.

### Task B11: k=1 and k=2 informative messages

Add specific user-facing messages for k=1 (can't do MA) and k=2 (het stats unreliable).

### Task B12: Warning color contrast fix

Line 13: Change `--warning` from #f59e0b to #d97706 (amber-600) for better contrast on white.

---

## Phase C: UX & Export (10 tasks)

### Task C1: Replace prompt() with modal dialogs

Lines 3579, 3614, 4480: Replace 3 prompt() calls with showInputModal().

### Task C2: Replace alert() with toast

Line 6383: Replace alert(msg) with showToast().

### Task C3: Demo dataset button

Add "Load Demo" button in onboarding/extract phase that populates a 6-study smoking cessation NMA dataset.

### Task C4: Focus trap in modals

Add Tab/Shift-Tab cycling within confirmOverlay and other modal overlays.

### Task C5: Print only active tab

Modify @media print (line 856) to hide non-active phases.

### Task C6: Print SVG CSS variable resolution

Ensure print media resolves CSS custom properties for SVG elements.

### Task C7: Context tooltips for stats terms

Add title attributes / info icons for P-score, SUCRA, prediction interval, I2, tau2 in the analysis output.

### Task C8: Print toast selector fix

Fix CSS selector mismatch: `.toast-container` vs `#toastContainer`.

### Task C9: PROSPERO placeholder warning

Add visual warning when protocol exports contain placeholder text.

### Task C10: Inline extract table validation

Add real-time validation on CI (lo < hi), positive N, numeric fields.

---

## Phase D: Security & Robustness (8 tasks)

### Task D1: Global unhandledrejection handler

Add window.addEventListener('unhandledrejection', ...) with msaLog + showToast.

### Task D2: Escape r.id in feedback buttons

Lines 4709-4714: Wrap r.id with escapeHtml() in onclick attributes.

### Task D3: CSP frame-ancestors

Add frame-ancestors 'self' to CSP meta tag (line 6).

### Task D4: Replace empty catches with logged catches

Find all `.catch(() => {})` and replace with `.catch(e => msaLog('warn', ...))`.

### Task D5: Pin CDN version

Change @huggingface/transformers@3 to specific pinned version.

### Task D6: k=2 heterogeneity warning

Add specific warning when k=2 that tau2/I2 estimates are unreliable.

### Task D7: Study CI level assumption warning

Add info text near extract table noting CIs are assumed 95%.

### Task D8: Add Phase A-D tests

Write comprehensive tests for all Phase A-D fixes.

---

## Verification (per phase)
1. All existing 211 + new tests pass (0 regressions)
2. Div balance: `<div[\s>]` count == `</div>` count
3. No `</script>` inside script blocks
4. No hardcoded z=1.96 (except Galbraith plot conventional bands)
5. 0 SEVERE JS console errors
6. `node --check` passes on extracted JS
