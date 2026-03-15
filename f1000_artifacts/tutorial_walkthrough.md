# MetaSprint NMA — Reviewer Walkthrough

## Prerequisites
- Modern browser (Chrome/Firefox/Edge) with JavaScript enabled
- File: metasprint-nma.html (single file, ~30,500 lines)
- No installation, no server, no R required

## Step 1: Open and Orient
1. Open `metasprint-nma.html` in your browser
2. Dismiss the tutorial prompt (or take the 30-second guided tour)
3. Note the phase navigation: Scope > Search > Screen > Extract > Analyze > Insights > Write

## Step 2: Load Demo Dataset
1. In the Analyze phase, find the "Example NMA Topics" dropdown
2. Select "Hasselblad 1998 Smoking Cessation (6 studies, 4 treatments)"
3. Click "Load Example" — 6 pairwise contrasts are loaded

## Step 3: Run NMA
1. Click "Run Network Meta-Analysis" (or press Ctrl+Enter)
2. Wait ~3 seconds for analysis to complete
3. Observe: league table, network graph, forest plot, P-scores

## Step 4: Verify Gold Standard
1. Scroll to "Published NMA Comparison" section
2. Check the "Gold Standard Regression Tests" badge — should show all checks passed
3. The comparison table shows app vs published values with T1-T4 tier labels

## Step 5: R Cross-Validation
### Option A: WebR (in-browser)
1. Scroll to "WebR: Validate with R in Your Browser"
2. Click "Load R & Validate" — wait ~30-60 seconds for first load
3. Review the comparison table: tau-squared, I-squared, treatment effects, P-scores
4. Status badge shows VALIDATED/PARTIAL/DIVERGENT

### Option B: Downloadable R Script
1. In the export toolbar, click "R Validation Script"
2. Copy or download the .R file
3. Run in R (>= 4.1) with netmeta installed
4. Review the PASS/FAIL output

## Step 6: Reviewer Evidence Packet
1. Click "Reviewer Packet" in the export toolbar
2. A new tab opens with: analysis summary, gold standard results, feature comparison, PRISMA status
3. Use Ctrl+P to save as PDF for supplementary material

## Step 7: Additional Diagnostics
- **Net heat plot**: Shows inconsistency contribution by comparison (Krahn 2013)
- **Rank clustering**: Groups treatments by similar P-scores (Papakonstantinou 2022)
- **Threshold analysis**: Shows how much evidence must change to alter rankings (Caldwell 2016)
- **Comparison-adjusted funnel**: Publication bias assessment with PET-PEESE
- **PRISMA-NMA checklist**: Interactive 32-item Hutton 2015 checklist

## Expected Output for Smoking Cessation Demo
- **Treatments**: No contact, Self-help, Individual counselling, Group counselling
- **Reference**: No contact (most connected)
- **Best treatment**: Group counselling (highest P-score)
- **tau-squared**: ~0.007 (DL)
- **I-squared**: ~23%
- **Gold standard**: All checks PASS within canonical tolerances
