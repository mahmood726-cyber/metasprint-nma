# NMA Code Review & Fix Design

**Date:** 2026-03-07
**Approach:** Single-pass fix, all P0/P1/P2 issues grouped by line region
**Target:** `metasprint-nma.html` (25,556 lines)

## Issues to Fix

### P0 — Critical (5)

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| P0-1 | Forest plot infinite tick loop | ~lines 11113, 11267 | Guard `range ≤ 0` → set `range = 1` |
| P0-2 | Bayesian refIdx hardcoded to 0 | ~line 10100 | Read from `nmaRefSelect` DOM element |
| P0-3 | P-score MC non-deterministic | ~line 10847 | Replace `Math.random()` with `mulberry32()` |
| P0-4 | Disconnected network filter name mismatch | ~line 11546 | Apply `normalizeTreatmentName()` before set check |
| P0-5 | Div balance verification | Structural | Count divs excluding `<script>` blocks, fix imbalances |

### P1 — High Priority (5)

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| P1-1 | League table red/green only (colorblind) | ~line 10703 | Add arrows/symbols, use blue/orange palette |
| P1-2 | Funnel plot missing x-axis labels | ~lines 11312-11334 | Add tick marks + significance contours |
| P1-3 | Network plot missing viewBox | ~line 10543 | Add `viewBox="0 0 W H"` from layout bounds |
| P1-4 | No P-score direction toggle | ~line 9999 | Add UI toggle for "lower is better" |
| P1-5 | k=2 heterogeneity warning | Engine | Add warning when k=2 for tau²/I² |

### P2 — Polish (5+)

| ID | Issue | Location | Fix |
|----|-------|----------|-----|
| P2-1 | Rank heatmap single-color ramp | ~line 10790 | Use YlGnBu diverging palette |
| P2-2 | Node-split uses z not t-distribution | ~line 10349 | Use t-dist with appropriate df |
| P2-3 | Dark mode ignores system preference | ~line 3306 | Check `prefers-color-scheme` on init |
| P2-4 | Empty catch blocks | Throughout | Replace with `msaLog('warn', ...)` |
| P2-5 | CDN version unpinned | ~line 25087 | Pin `@huggingface/transformers` to specific version |

## Approach

1. Read each affected region of the HTML file
2. Apply all fixes in that region before moving to next
3. Verify div balance after structural changes
4. Run 19 existing Selenium tests

## Constraints

- No architectural refactoring
- No new features beyond what fixes require
- No changes to test file unless needed for new behaviors
- Preserve all existing localStorage keys and IndexedDB schema
