# MetaSprint NMA Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform MetaSprint Dose-Response (19,308-line single-file HTML) into a Network Meta-Analysis platform with frequentist + Bayesian engines, league table, network plot, P-scores/SUCRA, component NMA, and consistency testing.

**Architecture:** Surgical refactor — copy base file, replace ~20% (Extract columns, Analysis engine, DR-specific viz) while keeping ~80% (UI framework, screening, GRADE, RoB, forest/funnel core, export, localStorage, Insights). New NMA engine code added in a dedicated section replacing lines 8173–8669 (dose-response functions).

**Tech Stack:** Single-file HTML/CSS/JS, SVG for visualizations, IndexedDB for storage, no external dependencies. Linear algebra (matrix ops) implemented in pure JS.

---

## Task 1: Copy base file + rename branding

**Files:**
- Create: `C:\Users\user\Downloads\metasprintnma\metasprint-nma.html`

**Step 1: Copy file**

```bash
cp "C:/Users/user/Downloads/metasprint-dose-response/metasprint-dose-response.html" "C:/Users/user/Downloads/metasprintnma/metasprint-nma.html"
```

**Step 2: Rename all branding strings**

Search-and-replace the following in `metasprint-nma.html`:

| Find | Replace |
|------|---------|
| `MetaSprint Dose-Response` | `MetaSprint NMA` |
| `Dose-Response Meta-Analysis Platform` | `Network Meta-Analysis Platform` |
| `Dose-Response` (in UI-facing strings only) | `Network Meta-Analysis` |
| `MetaSprintDoseResponse` (IndexedDB name) | `MetaSprintNMA` |
| `metaSprint_` (localStorage prefix) | `metaSprintNMA_` |
| `metasprint-dose-response-export.csv` | `metasprint-nma-export.csv` |

**CAUTION:** Do NOT blindly replace every "dose" — only UI labels and storage keys. JS variable names like `dose` in unreferenced functions will be removed in later tasks.

**Step 3: Update page title (line 6)**

```html
<title>MetaSprint NMA — Zero-Install Network Meta-Analysis Platform</title>
```

**Step 4: Update header (line ~998)**

Replace "Dose-Response" span with "NMA" span.

**Step 5: Verify the file still loads in browser**

Open in Chrome, confirm it loads with new branding. No JS errors in console.

---

## Task 2: Replace Extract table HTML + input mode

**Files:**
- Modify: `metasprint-nma.html` lines 1370–1395 (extract header area)

**Step 1: Replace input mode radio buttons (lines 1370–1374)**

Remove the one-stage/two-stage dose-response radio buttons. Replace with NMA input help text:

```html
<label style="font-size:0.82rem;color:var(--text-muted)">Input mode:</label>
<label style="font-size:0.82rem;cursor:pointer"><input type="radio" name="inputMode" value="effect" checked onchange="setInputMode('effect')"> Pairwise comparisons (one row per comparison)</label>
<label style="font-size:0.82rem;cursor:pointer"><input type="radio" name="inputMode" value="2x2" onchange="setInputMode('2x2')"> Raw 2x2 counts</label>
<label style="font-size:0.82rem;cursor:pointer"><input type="checkbox" id="publishableGateToggle" checked> Strict publishability gates</label>
<span id="inputModeHelp" style="font-size:0.78rem;color:var(--text-muted)">Enter one row per pairwise comparison: Treatment 1 vs Treatment 2, with effect estimate and CI. Multi-arm trials: enter all pairwise comparisons sharing the same Study ID.</span>
```

**Step 2: Replace extract table headers (lines 1379–1392)**

```html
<thead><tr id="extractHead">
  <th scope="col">Study ID</th><th scope="col">Trial ID *</th><th scope="col">NCT</th><th scope="col">PMID</th><th scope="col">DOI</th>
  <th scope="col">Outcome *</th><th scope="col">Timepoint *</th><th scope="col">Population</th><th scope="col">Verify</th>
  <th scope="col" title="Treatment/intervention arm">Treatment 1 *</th>
  <th scope="col" title="Comparator arm">Treatment 2 *</th>
  <th scope="col" title="Sample size in Treatment 1 arm">N1</th>
  <th scope="col" title="Sample size in Treatment 2 arm">N2</th>
  <th scope="col" title="Point estimate of the effect (Treatment 1 vs Treatment 2)">Effect *</th>
  <th scope="col" title="Lower bound of the confidence interval">Lower CI *</th>
  <th scope="col" title="Upper bound of the confidence interval">Upper CI *</th>
  <th scope="col" title="Standard error (optional; computed from CI if missing)">SE</th>
  <th scope="col" title="Type of effect measure">Type</th>
  <th scope="col" title="Subgroup label for stratified analysis">Subgroup</th>
  <th scope="col">Notes</th><th scope="col"></th>
</tr></thead>
```

---

## Task 3: Update addStudyRow() + study data model

**Files:**
- Modify: `metasprint-nma.html` lines 6699–6768 (addStudyRow function)

**Step 1: Replace dose-response fields in study object (lines 6727–6743)**

Remove:
```javascript
// Dose-response fields
dose: data.dose ?? null,
doseUnit: data.doseUnit || 'mg',
referenceDose: data.referenceDose ?? 0,
...
// Two-stage slope fields
slope: data.slope ?? null,
slopeSE: data.slopeSE ?? null,
```

Replace with:
```javascript
// NMA comparison fields
treatment1: data.treatment1 || '',
treatment2: data.treatment2 || '',
n1: data.n1 ?? null,
n2: data.n2 ?? null,
```

Keep all other fields (nTotal, effectEstimate, lowerCI, upperCI, se, effectType, etc.).

**Step 2: Update auto-compute from 2x2 (lines 6752–6763)**

Keep this block but ensure nTotal = n1 + n2 when both are present:
```javascript
if (study.n1 != null && study.n2 != null) {
  study.nTotal = study.n1 + study.n2;
}
```

---

## Task 4: Update renderExtractTable()

**Files:**
- Modify: `metasprint-nma.html` lines 6774–6828+ (renderExtractTable function)

**Step 1: Replace the header swap logic (lines 6780–6825)**

Remove the two-stage dose header. Replace with NMA columns:

For effect mode (`!is2x2`):
```javascript
head.innerHTML =
  '<th scope="col">Study ID</th>' +
  '<th scope="col">Trial ID *</th>' +
  '<th scope="col">NCT</th>' +
  '<th scope="col">PMID</th>' +
  '<th scope="col">DOI</th>' +
  '<th scope="col">Outcome *</th>' +
  '<th scope="col">Timepoint *</th>' +
  '<th scope="col">Population</th>' +
  '<th scope="col">Verify</th>' +
  '<th scope="col" title="Treatment/intervention arm">Treatment 1 *</th>' +
  '<th scope="col" title="Comparator arm">Treatment 2 *</th>' +
  '<th scope="col" title="N in Treatment 1 arm">N1</th>' +
  '<th scope="col" title="N in Treatment 2 arm">N2</th>' +
  '<th scope="col" title="Effect estimate (T1 vs T2)">Effect *</th>' +
  '<th scope="col" title="Lower CI">Lower CI *</th>' +
  '<th scope="col" title="Upper CI">Upper CI *</th>' +
  '<th scope="col" title="Standard error">SE</th>' +
  '<th scope="col">Type</th>' +
  '<th scope="col">Subgroup</th>' +
  '<th scope="col">Notes</th><th scope="col"></th>';
```

For 2x2 mode: keep existing 2x2 header (Events Int, Total Int, Events Ctrl, Total Ctrl) but rename "Intervention" → "Treatment 1" and "Control" → "Treatment 2".

**Step 2: Update body rendering**

Replace dose-specific input fields in the `<tr>` templates with `treatment1`, `treatment2`, `n1`, `n2` fields.

---

## Task 5: Replace Analysis phase HTML

**Files:**
- Modify: `metasprint-nma.html` lines 1425–1475 (phase-analyze section)

**Step 1: Replace the Analyze phase HTML**

```html
<!-- Phase 6: Analyze -->
<section id="phase-analyze" class="phase" role="tabpanel" aria-labelledby="tab-analyze" tabindex="-1">
  <h2>Network Meta-Analysis Dashboard</h2>
  <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
    <button class="btn-success" onclick="runAnalysis()">Run Network Meta-Analysis</button>
    <button class="btn-outline" onclick="handoffToTruthCert()">Send to TruthCert</button>
    <button onclick="runLOOAnalysis()">Leave-One-Out</button>
    <label for="confLevelSelect" style="font-size:0.8rem;color:var(--text-muted)">Confidence:</label>
    <select id="confLevelSelect" style="padding:4px 8px;font-size:0.82rem;border:1px solid var(--border);border-radius:var(--radius)">
      <option value="0.90">90%</option>
      <option value="0.95" selected>95%</option>
      <option value="0.99">99%</option>
    </select>
    <label for="methodSelect" style="font-size:0.8rem;color:var(--text-muted)">Pooling:</label>
    <select id="methodSelect" style="padding:4px 8px;font-size:0.82rem;border:1px solid var(--border);border-radius:var(--radius)">
      <option value="DL" selected>DL (DerSimonian-Laird)</option>
      <option value="DL-HKSJ">DL + HKSJ adjustment</option>
      <option value="FE">Fixed Effect (IV)</option>
    </select>
    <label for="nmaModelSelect" style="font-size:0.8rem;color:var(--text-muted)">NMA Engine:</label>
    <select id="nmaModelSelect" style="padding:4px 8px;font-size:0.82rem;border:1px solid var(--border);border-radius:var(--radius)">
      <option value="frequentist" selected>Frequentist (graph-theoretic)</option>
      <option value="bayesian">Bayesian (MCMC)</option>
    </select>
    <label for="nmaRefSelect" style="font-size:0.8rem;color:var(--text-muted)">Reference:</label>
    <select id="nmaRefSelect" style="padding:4px 8px;font-size:0.82rem;border:1px solid var(--border);border-radius:var(--radius)">
      <option value="auto" selected>Auto (most connected)</option>
    </select>
  </div>
  <div id="analysisWarnings" style="margin-bottom:8px"></div>
  <div class="analysis-summary" id="analysisSummary"></div>
  <div id="networkPlotContainer" style="margin-top:16px"></div>
  <div id="leagueTableContainer" style="margin-top:16px"></div>
  <div class="analysis-plots">
    <div id="forestPlotContainer"></div>
    <div id="funnelPlotContainer"></div>
  </div>
  <div id="analysisExport" style="margin-top:12px;display:none">
    <button class="btn-outline" onclick="exportPlotSVG('forestPlotContainer','forest-plot.svg')">Export Forest SVG</button>
    <button class="btn-outline" onclick="exportPlotSVG('funnelPlotContainer','funnel-plot.svg')">Export Funnel SVG</button>
    <button class="btn-outline" onclick="exportPlotSVG('networkPlotContainer','network-plot.svg')">Export Network SVG</button>
    <button class="btn-outline" onclick="exportLeagueTableCSV()">Export League Table CSV</button>
    <button class="btn-outline" onclick="copyAnalysisSummary()">Copy Statistics</button>
  </div>
  <div id="pscoreContainer" style="margin-top:20px"></div>
  <div id="rankProbContainer" style="margin-top:20px"></div>
  <div id="consistencyContainer" style="margin-top:20px"></div>
  <div id="componentContainer" style="margin-top:20px"></div>
  <div id="looContainer" style="margin-top:20px"></div>
  <div id="eggerContainer" style="margin-top:12px"></div>
  <div id="gradeNntRow" style="margin-top:20px;display:none;gap:16px;flex-wrap:wrap">
    <div id="gradeContainer" style="flex:1;min-width:320px"></div>
    <div id="nntContainer" style="flex:1;min-width:280px"></div>
  </div>
  <div id="subgroupContainer" style="margin-top:20px"></div>
  <div id="cumulativeContainer" style="margin-top:20px"></div>
  <div id="trimFillContainer" style="margin-top:20px"></div>
  <div id="fragilityContainer" style="margin-top:20px"></div>
  <div id="metaRegressionContainer" style="margin-top:20px"></div>
</section>
```

Note: Removed `doseResponseCurveContainer` and `drModelSelect`. Added `networkPlotContainer`, `leagueTableContainer`, `pscoreContainer`, `rankProbContainer`, `consistencyContainer`, `componentContainer`, `nmaModelSelect`, `nmaRefSelect`.

---

## Task 6: Remove dose-response JS functions

**Files:**
- Modify: `metasprint-nma.html` lines 8173–8669

**Step 1: Delete all dose-response functions**

Remove these functions entirely (lines ~8173–8669):
- `prepareDoseResponseData()`
- `fitLinearDR()`
- `fitQuadraticDR()`
- `fitEmaxDR()`
- `_emaxSSR()`
- `compareDoseResponseModels()`
- `renderDoseResponseAnalysis()`
- `renderDoseResponseCurveSVG()`

**Step 2: Replace with a placeholder comment**

```javascript
// ============================================================
// NETWORK META-ANALYSIS ENGINE (replaces dose-response code)
// ============================================================
// See Task 7–12 for NMA engine implementation
```

---

## Task 7: Implement NMA core — network graph construction + linear algebra utilities

**Files:**
- Modify: `metasprint-nma.html` (insert after the placeholder from Task 6)

**Step 1: Add linear algebra helper functions**

```javascript
// ============================================================
// LINEAR ALGEBRA UTILITIES
// ============================================================

/** Create m x n zero matrix */
function matZeros(m, n) {
  return Array.from({ length: m }, () => new Float64Array(n));
}

/** Matrix multiply A (m x p) * B (p x n) -> C (m x n) */
function matMul(A, B) {
  const m = A.length, p = A[0].length, n = B[0].length;
  const C = matZeros(m, n);
  for (let i = 0; i < m; i++)
    for (let k = 0; k < p; k++) {
      const a = A[i][k];
      if (a === 0) continue;
      for (let j = 0; j < n; j++) C[i][j] += a * B[k][j];
    }
  return C;
}

/** Transpose matrix */
function matT(A) {
  const m = A.length, n = A[0].length;
  const T = matZeros(n, m);
  for (let i = 0; i < m; i++)
    for (let j = 0; j < n; j++) T[j][i] = A[i][j];
  return T;
}

/** Moore-Penrose pseudoinverse via SVD-free approach for symmetric PSD:
 *  L+ where L is the graph Laplacian. Uses eigendecomposition for small matrices.
 *  For NMA: treatments are typically <30, so O(n^3) is fine.
 */
function matPseudoInverse(A) {
  const n = A.length;
  // LU-based general inverse with regularization for singular matrices
  // Add small epsilon to diagonal, invert, then project out null space
  const eps = 1e-12;
  const B = matZeros(n, n);
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) B[i][j] = A[i][j] + (i === j ? eps : 0);
  return matInvert(B);
}

/** Invert n x n matrix via Gauss-Jordan elimination */
function matInvert(A) {
  const n = A.length;
  // Augmented matrix [A | I]
  const aug = Array.from({ length: n }, (_, i) => {
    const row = new Float64Array(2 * n);
    for (let j = 0; j < n; j++) row[j] = A[i][j];
    row[n + i] = 1;
    return row;
  });
  for (let col = 0; col < n; col++) {
    // Partial pivoting
    let maxVal = Math.abs(aug[col][col]), maxRow = col;
    for (let row = col + 1; row < n; row++) {
      if (Math.abs(aug[row][col]) > maxVal) { maxVal = Math.abs(aug[row][col]); maxRow = row; }
    }
    if (maxVal < 1e-15) continue; // singular column
    if (maxRow !== col) { const tmp = aug[col]; aug[col] = aug[maxRow]; aug[maxRow] = tmp; }
    const pivot = aug[col][col];
    for (let j = 0; j < 2 * n; j++) aug[col][j] /= pivot;
    for (let row = 0; row < n; row++) {
      if (row === col) continue;
      const factor = aug[row][col];
      for (let j = 0; j < 2 * n; j++) aug[row][j] -= factor * aug[col][j];
    }
  }
  const inv = matZeros(n, n);
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) inv[i][j] = aug[i][n + j];
  return inv;
}

/** Diagonal matrix from array */
function matDiag(arr) {
  const n = arr.length;
  const D = matZeros(n, n);
  for (let i = 0; i < n; i++) D[i][i] = arr[i];
  return D;
}
```

**Step 2: Add network graph construction**

```javascript
// ============================================================
// NETWORK GRAPH CONSTRUCTION
// ============================================================

/**
 * Build network structure from extracted studies.
 * Returns: { treatments, edges, comparisons, B, adjMatrix, components }
 * treatments: sorted unique treatment names
 * edges: [{t1, t2, studies: [...], nStudies, effectEstimate, se, weight}]
 * B: design (edge-incidence) matrix (nEdges x nTreatments)
 * components: array of arrays (connected components)
 */
function buildNetworkGraph(studies) {
  // Collect all unique treatments
  const treatSet = new Set();
  const edgeMap = new Map(); // "t1||t2" -> {studies, effects}

  for (const s of studies) {
    if (!s.treatment1 || !s.treatment2) continue;
    if (s.effectEstimate == null || (s.lowerCI == null && s.se == null)) continue;
    const t1 = s.treatment1.trim();
    const t2 = s.treatment2.trim();
    if (t1 === t2) continue;
    treatSet.add(t1);
    treatSet.add(t2);
    // Canonical edge key: alphabetically sorted
    const [a, b] = [t1, t2].sort();
    const key = a + '||' + b;
    if (!edgeMap.has(key)) edgeMap.set(key, { t1: a, t2: b, studies: [] });
    const direction = t1 === a ? 1 : -1; // flip effect if order reversed
    const sei = s.se ?? (s.lowerCI != null && s.upperCI != null
      ? (s.upperCI - s.lowerCI) / (2 * normalQuantile(0.975))
      : null);
    if (sei == null || sei <= 0) continue;
    edgeMap.get(key).studies.push({
      ...s,
      directedEffect: s.effectEstimate * direction,
      se: sei,
      direction
    });
  }

  const treatments = [...treatSet].sort();
  const tIndex = new Map(treatments.map((t, i) => [t, i]));
  const nT = treatments.length;

  // Pool each edge (pairwise meta-analysis per comparison)
  const edges = [];
  for (const [key, edge] of edgeMap) {
    if (edge.studies.length === 0) continue;
    // Inverse-variance pooling within this comparison
    let sumW = 0, sumWY = 0;
    for (const s of edge.studies) {
      const w = 1 / (s.se * s.se);
      sumW += w;
      sumWY += w * s.directedEffect;
    }
    const pooledEffect = sumWY / sumW;
    const pooledSE = 1 / Math.sqrt(sumW);
    edges.push({
      t1: edge.t1, t2: edge.t2,
      t1Idx: tIndex.get(edge.t1),
      t2Idx: tIndex.get(edge.t2),
      studies: edge.studies,
      nStudies: edge.studies.length,
      effectEstimate: pooledEffect,
      se: pooledSE,
      weight: sumW
    });
  }

  // Design matrix B: each row = edge, cols = treatments
  // Convention: B[e][t1] = -1, B[e][t2] = +1 (effect = t2 - t1)
  const nE = edges.length;
  const B = matZeros(nE, nT);
  for (let e = 0; e < nE; e++) {
    B[e][edges[e].t1Idx] = -1;
    B[e][edges[e].t2Idx] = 1;
  }

  // Adjacency matrix (for visualization and connectivity)
  const adjMatrix = matZeros(nT, nT);
  for (const edge of edges) {
    adjMatrix[edge.t1Idx][edge.t2Idx] = edge.nStudies;
    adjMatrix[edge.t2Idx][edge.t1Idx] = edge.nStudies;
  }

  // Connected components via BFS
  const visited = new Array(nT).fill(false);
  const components = [];
  for (let start = 0; start < nT; start++) {
    if (visited[start]) continue;
    const comp = [];
    const queue = [start];
    visited[start] = true;
    while (queue.length > 0) {
      const node = queue.shift();
      comp.push(node);
      for (let j = 0; j < nT; j++) {
        if (!visited[j] && adjMatrix[node][j] > 0) {
          visited[j] = true;
          queue.push(j);
        }
      }
    }
    components.push(comp);
  }

  return { treatments, tIndex, edges, B, adjMatrix, components, nT, nE };
}
```

---

## Task 8: Implement frequentist NMA engine

**Files:**
- Modify: `metasprint-nma.html` (insert after Task 7 code)

**Step 1: Graph-theoretic NMA (Rucker 2012)**

```javascript
// ============================================================
// FREQUENTIST NMA ENGINE (Rucker 2012, graph-theoretic)
// ============================================================

/**
 * Run frequentist NMA.
 * @param {object} network - from buildNetworkGraph()
 * @param {number} confLevel - e.g. 0.95
 * @returns {object} { d (treatment effects vs ref), V (variance-covariance),
 *   leagueTable, pscores, Qtotal, Qhet, Qincon, refTreatment, ... }
 */
function runFrequentistNMA(network, confLevel) {
  const { treatments, tIndex, edges, B, nT, nE, components } = network;
  if (nE === 0 || nT < 2) return null;

  // Check connectivity
  const mainComponent = components.reduce((a, b) => a.length >= b.length ? a : b, []);
  if (mainComponent.length < nT) {
    // Disconnected network — warn but proceed with largest component
  }

  // Choose reference: most connected treatment (highest degree)
  const refSelect = document.getElementById('nmaRefSelect')?.value || 'auto';
  let refIdx;
  if (refSelect === 'auto') {
    const degree = new Array(nT).fill(0);
    for (const e of edges) { degree[e.t1Idx]++; degree[e.t2Idx]++; }
    refIdx = degree.indexOf(Math.max(...degree));
  } else {
    refIdx = tIndex.get(refSelect) ?? 0;
  }
  const refTreatment = treatments[refIdx];

  // Observed effects vector y and weight matrix W
  const y = new Float64Array(nE);
  const w = new Float64Array(nE);
  for (let e = 0; e < nE; e++) {
    y[e] = edges[e].effectEstimate;
    w[e] = edges[e].weight; // 1/se^2
  }
  const W = matDiag(w);

  // Common tau^2 estimation (DL method of moments)
  // Q = y^T (W - W B (B^T W B)^-1 B^T W) y
  const BT = matT(B);
  const BTWB = matMul(matMul(BT, W), B); // nT x nT Laplacian
  const L = BTWB;
  const Linv = matPseudoInverse(L);

  // Hat matrix H = B Linv B^T W
  const H = matMul(matMul(matMul(B, Linv), BT), W);

  // Residuals and Q statistic
  const yHat = new Float64Array(nE);
  for (let e = 0; e < nE; e++) {
    let s = 0;
    for (let j = 0; j < nE; j++) s += H[e][j] * y[j];
    yHat[e] = s;
  }
  let Qtotal = 0;
  for (let e = 0; e < nE; e++) {
    Qtotal += w[e] * (y[e] - yHat[e]) * (y[e] - yHat[e]);
  }

  // Degrees of freedom
  const dfTotal = nE - (nT - 1); // total df

  // DL tau^2 estimate
  // tau^2 = max(0, (Q - df) / (sum_w - trace(W^2 Linv)))
  let trWsq = 0;
  for (let e = 0; e < nE; e++) trWsq += w[e] * w[e];
  // Simplified: tau^2 = max(0, (Q - dfTotal) / C) where C = sum(w) - sum(w^2)/sum(w)
  const sumW = w.reduce((a, b) => a + b, 0);
  const sumW2 = w.reduce((a, b) => a + b * b, 0);
  const C_dl = sumW - sumW2 / sumW;
  let tau2 = dfTotal > 0 ? Math.max(0, (Qtotal - dfTotal) / C_dl) : 0;

  // Re-estimate with random effects weights
  const wRE = new Float64Array(nE);
  for (let e = 0; e < nE; e++) {
    wRE[e] = 1 / (1 / w[e] + tau2);
  }
  const WRE = matDiag(wRE);
  const BTWB_RE = matMul(matMul(BT, WRE), B);
  const Linv_RE = matPseudoInverse(BTWB_RE);

  // Network estimates: d = Linv B^T W_RE y
  const BTWREy = new Float64Array(nT);
  for (let t = 0; t < nT; t++) {
    let s = 0;
    for (let e = 0; e < nE; e++) s += BT[t][e] * wRE[e] * y[e];
    BTWREy[t] = s;
  }
  const d = new Float64Array(nT); // treatment effects (relative to reference)
  for (let t = 0; t < nT; t++) {
    let s = 0;
    for (let j = 0; j < nT; j++) s += Linv_RE[t][j] * BTWREy[j];
    d[t] = s;
  }
  // Center on reference treatment
  const dRef = d[refIdx];
  for (let t = 0; t < nT; t++) d[t] -= dRef;

  // Variance-covariance of d (relative to ref)
  // V = Linv_RE, but centered
  const V = matZeros(nT, nT);
  for (let i = 0; i < nT; i++)
    for (let j = 0; j < nT; j++)
      V[i][j] = Linv_RE[i][j] - Linv_RE[i][refIdx] - Linv_RE[refIdx][j] + Linv_RE[refIdx][refIdx];

  const zCrit = normalQuantile(1 - (1 - confLevel) / 2);

  // Build league table (all pairwise)
  const leagueTable = [];
  for (let i = 0; i < nT; i++) {
    for (let j = 0; j < nT; j++) {
      if (i === j) continue;
      const dij = d[i] - d[j];
      const varij = V[i][i] + V[j][j] - 2 * V[i][j];
      const seij = Math.sqrt(Math.max(0, varij));
      const lo = dij - zCrit * seij;
      const hi = dij + zCrit * seij;
      const pVal = seij > 0 ? 2 * (1 - normalCDF(Math.abs(dij / seij))) : 1;
      leagueTable.push({
        t1: treatments[i], t2: treatments[j],
        t1Idx: i, t2Idx: j,
        effect: dij, se: seij, lo, hi, pValue: pVal
      });
    }
  }

  // P-scores (Rucker & Schwarzer 2015)
  const pscores = new Float64Array(nT);
  for (let i = 0; i < nT; i++) {
    let score = 0;
    for (let j = 0; j < nT; j++) {
      if (i === j) continue;
      const dij = d[i] - d[j];
      const varij = V[i][i] + V[j][j] - 2 * V[i][j];
      const seij = Math.sqrt(Math.max(1e-15, varij));
      score += normalCDF(dij / seij);
    }
    pscores[i] = score / (nT - 1);
  }

  // Q decomposition (heterogeneity vs inconsistency)
  // Q_heterogeneity: within-design Q
  // Q_inconsistency: Q_total - Q_het (between-design)
  const H_RE = matMul(matMul(matMul(B, Linv_RE), BT), WRE);
  const yHatRE = new Float64Array(nE);
  for (let e = 0; e < nE; e++) {
    let s = 0;
    for (let j = 0; j < nE; j++) s += H_RE[e][j] * y[j];
    yHatRE[e] = s;
  }
  let Q_RE = 0;
  for (let e = 0; e < nE; e++) {
    Q_RE += wRE[e] * (y[e] - yHatRE[e]) * (y[e] - yHatRE[e]);
  }

  // I^2 global
  const I2global = dfTotal > 0 ? Math.max(0, (Qtotal - dfTotal) / Qtotal * 100) : 0;

  // Hat matrix for component NMA contribution
  const hatMatrix = H_RE;

  return {
    d, V, tau2, Qtotal, dfTotal, I2global, Q_RE,
    leagueTable, pscores, treatments, refTreatment, refIdx,
    edges, nT, nE, components, hatMatrix, zCrit, confLevel,
    network
  };
}
```

---

## Task 9: Implement Bayesian NMA engine

**Files:**
- Modify: `metasprint-nma.html` (insert after Task 8 code)

**Step 1: Metropolis-Hastings MCMC for Lu & Ades consistency model**

```javascript
// ============================================================
// BAYESIAN NMA ENGINE (Lu & Ades, Metropolis-Hastings)
// ============================================================

/**
 * Run Bayesian NMA with MCMC.
 * @param {object} network - from buildNetworkGraph()
 * @param {number} confLevel
 * @param {object} opts - { nChains: 4, nWarmup: 5000, nSamples: 10000 }
 */
function runBayesianNMA(network, confLevel, opts) {
  opts = opts || {};
  const nChains = opts.nChains ?? 4;
  const nWarmup = opts.nWarmup ?? 2000;
  const nSamples = opts.nSamples ?? 5000;
  const { treatments, tIndex, edges, nT, nE } = network;
  if (nE === 0 || nT < 2) return null;

  const refIdx = 0; // first treatment as reference for Bayesian

  // Data: y[e] = observed effect, se[e] = observed SE
  const y = edges.map(e => e.effectEstimate);
  const se = edges.map(e => e.se);
  const t1Idx = edges.map(e => e.t1Idx);
  const t2Idx = edges.map(e => e.t2Idx);

  // Log-likelihood: sum_e -0.5 * ((y[e] - (d[t2]-d[t1]))^2 / (se[e]^2 + tau^2))
  //                       -0.5 * log(se[e]^2 + tau^2)
  function logLik(d, tau2) {
    let ll = 0;
    for (let e = 0; e < nE; e++) {
      const mu = d[t2Idx[e]] - d[t1Idx[e]];
      const v = se[e] * se[e] + tau2;
      ll += -0.5 * ((y[e] - mu) * (y[e] - mu) / v + Math.log(v));
    }
    return ll;
  }

  // Prior: d[t] ~ N(0, 100), tau ~ HalfNormal(0, 1)
  function logPrior(d, tau2) {
    let lp = 0;
    for (let t = 0; t < nT; t++) {
      if (t === refIdx) continue;
      lp += -0.5 * d[t] * d[t] / 100;
    }
    // HalfNormal(0,1) on tau => log(2/(sqrt(2pi))) - tau^2/2
    const tau = Math.sqrt(tau2);
    lp += -tau * tau / 2;
    return lp;
  }

  // Run chains
  const allSamples = [];
  const rng = xoshiro128ss(42); // seeded PRNG

  for (let chain = 0; chain < nChains; chain++) {
    // Initialize
    const d = new Float64Array(nT);
    for (let t = 0; t < nT; t++) d[t] = (chain * 0.5 - 1) * 0.1;
    d[refIdx] = 0;
    let tau2 = 0.1 + chain * 0.05;
    let stepD = 0.1, stepTau = 0.05;
    let acceptD = 0, acceptTau = 0, totalD = 0, totalTau = 0;

    const samples = [];

    for (let iter = 0; iter < nWarmup + nSamples; iter++) {
      // Update each d[t] (Gibbs-within-Metropolis)
      for (let t = 0; t < nT; t++) {
        if (t === refIdx) continue;
        const dOld = d[t];
        const logPOld = logLik(d, tau2) + logPrior(d, tau2);
        d[t] += normalRandom(rng) * stepD;
        const logPNew = logLik(d, tau2) + logPrior(d, tau2);
        totalD++;
        if (Math.log(rng()) < logPNew - logPOld) {
          acceptD++;
        } else {
          d[t] = dOld;
        }
      }

      // Update tau2
      const tau2Old = tau2;
      const logPOld = logLik(d, tau2) + logPrior(d, tau2);
      const proposal = tau2 + normalRandom(rng) * stepTau;
      if (proposal > 0) {
        tau2 = proposal;
        const logPNew = logLik(d, tau2) + logPrior(d, tau2);
        totalTau++;
        if (Math.log(rng()) < logPNew - logPOld) {
          acceptTau++;
        } else {
          tau2 = tau2Old;
        }
      }

      // Adapt step sizes during warmup
      if (iter < nWarmup && iter > 0 && iter % 100 === 0) {
        const rateD = acceptD / totalD;
        const rateTau = acceptTau / Math.max(1, totalTau);
        if (rateD < 0.2) stepD *= 0.8;
        else if (rateD > 0.5) stepD *= 1.2;
        if (rateTau < 0.2) stepTau *= 0.8;
        else if (rateTau > 0.5) stepTau *= 1.2;
        acceptD = acceptTau = totalD = totalTau = 0;
      }

      // Store post-warmup samples
      if (iter >= nWarmup) {
        samples.push({ d: Float64Array.from(d), tau2 });
      }
    }
    allSamples.push(samples);
  }

  // Combine chains and compute summaries
  const combined = allSamples.flat();
  const nTotal = combined.length;

  // Posterior summaries for d[t] vs ref
  const zCrit = normalQuantile(1 - (1 - confLevel) / 2);
  const credLo = (1 - confLevel) / 2;
  const credHi = 1 - credLo;

  const dSummary = [];
  for (let t = 0; t < nT; t++) {
    const vals = combined.map(s => s.d[t]).sort((a, b) => a - b);
    const median = vals[Math.floor(nTotal * 0.5)];
    const lo = vals[Math.floor(nTotal * credLo)];
    const hi = vals[Math.floor(nTotal * credHi)];
    const mean = vals.reduce((a, b) => a + b, 0) / nTotal;
    dSummary.push({ treatment: treatments[t], mean, median, lo, hi });
  }

  // SUCRA: for each sample, rank treatments, then compute P(rank=r) for each
  const rankProbs = matZeros(nT, nT); // [treatment][rank]
  const sucra = new Float64Array(nT);

  for (const sample of combined) {
    // Rank: higher d = better (rank 1 = best)
    const indices = Array.from({ length: nT }, (_, i) => i);
    indices.sort((a, b) => sample.d[b] - sample.d[a]);
    for (let rank = 0; rank < nT; rank++) {
      rankProbs[indices[rank]][rank] += 1 / nTotal;
    }
  }

  for (let t = 0; t < nT; t++) {
    // SUCRA = sum over r of P(rank <= r) * 1/(nT-1) = (mean rank - 1) / (nT - 1)
    let meanRank = 0;
    for (let r = 0; r < nT; r++) meanRank += rankProbs[t][r] * (r + 1);
    sucra[t] = (nT - meanRank) / (nT - 1);
  }

  // Posterior tau2 summary
  const tau2Vals = combined.map(s => s.tau2).sort((a, b) => a - b);
  const tau2Summary = {
    median: tau2Vals[Math.floor(nTotal * 0.5)],
    lo: tau2Vals[Math.floor(nTotal * credLo)],
    hi: tau2Vals[Math.floor(nTotal * credHi)]
  };

  // Gelman-Rubin R-hat (simplified)
  const rhat = [];
  for (let t = 0; t < nT; t++) {
    const chainMeans = allSamples.map(ch => {
      const vals = ch.map(s => s.d[t]);
      return vals.reduce((a, b) => a + b, 0) / vals.length;
    });
    const grandMean = chainMeans.reduce((a, b) => a + b, 0) / nChains;
    const B_var = nSamples / (nChains - 1) * chainMeans.reduce((a, m) => a + (m - grandMean) ** 2, 0);
    const W_var = allSamples.reduce((a, ch) => {
      const mean = ch.map(s => s.d[t]).reduce((a, b) => a + b, 0) / ch.length;
      return a + ch.map(s => s.d[t]).reduce((s, v) => s + (v - mean) ** 2, 0) / (ch.length - 1);
    }, 0) / nChains;
    const varPlus = (1 - 1 / nSamples) * W_var + B_var / nSamples;
    rhat.push(W_var > 0 ? Math.sqrt(varPlus / W_var) : 1);
  }

  // Build league table from posterior
  const leagueTable = [];
  for (let i = 0; i < nT; i++) {
    for (let j = 0; j < nT; j++) {
      if (i === j) continue;
      const diffs = combined.map(s => s.d[i] - s.d[j]).sort((a, b) => a - b);
      const median = diffs[Math.floor(nTotal * 0.5)];
      const lo = diffs[Math.floor(nTotal * credLo)];
      const hi = diffs[Math.floor(nTotal * credHi)];
      leagueTable.push({ t1: treatments[i], t2: treatments[j], effect: median, lo, hi });
    }
  }

  return {
    dSummary, tau2Summary, sucra, rankProbs, leagueTable,
    rhat, treatments, refTreatment: treatments[refIdx], refIdx,
    nChains, nWarmup, nSamples: nSamples, nT, nE: nE,
    confLevel, network
  };
}

/** Normal random from uniform via Box-Muller */
function normalRandom(rng) {
  const u1 = rng(), u2 = rng();
  return Math.sqrt(-2 * Math.log(u1 + 1e-15)) * Math.cos(2 * Math.PI * u2);
}

/** xoshiro128** seeded PRNG (from existing MetaSprint codebase) */
// NOTE: This function likely already exists in the base file — reuse it.
// If not present, add the standard xoshiro128** implementation here.
```

---

## Task 10: Implement node-splitting consistency test + component NMA

**Files:**
- Modify: `metasprint-nma.html` (insert after Task 9 code)

**Step 1: Node-splitting (Dias 2010)**

```javascript
// ============================================================
// CONSISTENCY TESTING
// ============================================================

/**
 * Node-splitting: for each comparison with a closed loop,
 * compare direct vs indirect evidence.
 */
function runNodeSplitting(network, confLevel) {
  const { treatments, tIndex, edges, nT, nE } = network;
  const results = [];

  for (const edge of edges) {
    const i = edge.t1Idx, j = edge.t2Idx;

    // Direct evidence: studies directly comparing i and j
    const directEffect = edge.effectEstimate;
    const directSE = edge.se;

    // Indirect evidence: run NMA excluding this edge
    const reducedEdges = edges.filter(e => !(e.t1Idx === i && e.t2Idx === j));
    if (reducedEdges.length < nT - 2) continue; // not enough edges for indirect

    // Build reduced network
    const reducedNetwork = {
      ...network,
      edges: reducedEdges,
      nE: reducedEdges.length,
      B: matZeros(reducedEdges.length, nT)
    };
    for (let e = 0; e < reducedEdges.length; e++) {
      reducedNetwork.B[e][reducedEdges[e].t1Idx] = -1;
      reducedNetwork.B[e][reducedEdges[e].t2Idx] = 1;
    }

    // Check if i and j are still connected in reduced network
    const visited = new Set();
    const queue = [i];
    visited.add(i);
    while (queue.length > 0) {
      const node = queue.shift();
      for (const re of reducedEdges) {
        const other = re.t1Idx === node ? re.t2Idx : (re.t2Idx === node ? re.t1Idx : -1);
        if (other >= 0 && !visited.has(other)) {
          visited.add(other);
          queue.push(other);
        }
      }
    }
    if (!visited.has(j)) continue; // no indirect path

    // Run NMA on reduced network
    const reducedResult = runFrequentistNMA(reducedNetwork, confLevel);
    if (!reducedResult) continue;

    // Indirect effect = d[i] - d[j] from reduced NMA
    const indirectEffect = reducedResult.d[i] - reducedResult.d[j];
    // Flip sign to match edge direction (t1 -> t2)
    const indirectEffectAligned = -(indirectEffect); // t1 vs t2
    const indirectVar = reducedResult.V[i][i] + reducedResult.V[j][j] - 2 * reducedResult.V[i][j];
    const indirectSE = Math.sqrt(Math.max(0, indirectVar));

    // Test: z = (direct - indirect) / sqrt(SE_d^2 + SE_i^2)
    const diff = directEffect - indirectEffectAligned;
    const diffSE = Math.sqrt(directSE * directSE + indirectSE * indirectSE);
    const z = diffSE > 0 ? diff / diffSE : 0;
    const pValue = 2 * (1 - normalCDF(Math.abs(z)));

    results.push({
      t1: edge.t1, t2: edge.t2,
      directEffect, directSE,
      indirectEffect: indirectEffectAligned, indirectSE,
      diff, diffSE, z, pValue,
      inconsistent: pValue < 0.05
    });
  }

  return results;
}

// ============================================================
// COMPONENT NMA (Papakonstantinou 2018)
// ============================================================

/**
 * Compute contribution matrix: how much each direct comparison
 * contributes to each network estimate.
 * Returns matrix[nE x nE]: contribution[network_estimate][direct_comparison]
 */
function computeContributionMatrix(nmaResult) {
  // The hat matrix H already gives us this:
  // H[e][e'] = proportion of network estimate for edge e that comes from direct evidence e'
  // Normalize rows to percentages
  const { hatMatrix, nE } = nmaResult;
  const contribution = matZeros(nE, nE);
  for (let i = 0; i < nE; i++) {
    let rowSum = 0;
    for (let j = 0; j < nE; j++) rowSum += Math.abs(hatMatrix[i][j]);
    for (let j = 0; j < nE; j++) {
      contribution[i][j] = rowSum > 0 ? Math.abs(hatMatrix[i][j]) / rowSum * 100 : 0;
    }
  }
  return contribution;
}
```

---

## Task 11: Implement NMA visualizations

**Files:**
- Modify: `metasprint-nma.html` (insert after Task 10 code)

**Step 1: Network plot (force-directed SVG)**

```javascript
// ============================================================
// NMA VISUALIZATIONS
// ============================================================

/** Render network plot as SVG (force-directed layout) */
function renderNetworkPlot(network) {
  const { treatments, edges, nT, adjMatrix } = network;
  if (nT === 0) return '<p>No treatments in network</p>';

  const W = 600, H = 500;
  const theme = getThemeColors();
  const isDark = document.body.classList.contains('dark-mode');

  // Initialize positions in a circle
  const positions = treatments.map((_, i) => ({
    x: W / 2 + 200 * Math.cos(2 * Math.PI * i / nT),
    y: H / 2 + 200 * Math.sin(2 * Math.PI * i / nT)
  }));

  // Simple force-directed layout (50 iterations)
  for (let iter = 0; iter < 80; iter++) {
    const forces = positions.map(() => ({ fx: 0, fy: 0 }));
    // Repulsive force between all nodes
    for (let i = 0; i < nT; i++) {
      for (let j = i + 1; j < nT; j++) {
        const dx = positions[i].x - positions[j].x;
        const dy = positions[i].y - positions[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy) + 0.1;
        const repulse = 8000 / (dist * dist);
        forces[i].fx += repulse * dx / dist;
        forces[i].fy += repulse * dy / dist;
        forces[j].fx -= repulse * dx / dist;
        forces[j].fy -= repulse * dy / dist;
      }
    }
    // Attractive force along edges
    for (const e of edges) {
      const dx = positions[e.t2Idx].x - positions[e.t1Idx].x;
      const dy = positions[e.t2Idx].y - positions[e.t1Idx].y;
      const dist = Math.sqrt(dx * dx + dy * dy) + 0.1;
      const attract = dist * 0.01;
      forces[e.t1Idx].fx += attract * dx / dist;
      forces[e.t1Idx].fy += attract * dy / dist;
      forces[e.t2Idx].fx -= attract * dx / dist;
      forces[e.t2Idx].fy -= attract * dy / dist;
    }
    // Center gravity
    for (let i = 0; i < nT; i++) {
      forces[i].fx += (W / 2 - positions[i].x) * 0.005;
      forces[i].fy += (H / 2 - positions[i].y) * 0.005;
    }
    // Apply
    const cooling = 1 - iter / 100;
    for (let i = 0; i < nT; i++) {
      positions[i].x += forces[i].fx * cooling;
      positions[i].y += forces[i].fy * cooling;
      // Clamp to bounds
      positions[i].x = Math.max(60, Math.min(W - 60, positions[i].x));
      positions[i].y = Math.max(40, Math.min(H - 40, positions[i].y));
    }
  }

  // Compute node sizes (proportional to total N across all comparisons)
  const nodeN = new Array(nT).fill(0);
  for (const e of edges) {
    for (const s of e.studies) {
      nodeN[e.t1Idx] += (s.n1 ?? s.nTotal ?? 0) / 2;
      nodeN[e.t2Idx] += (s.n2 ?? s.nTotal ?? 0) / 2;
    }
  }
  const maxN = Math.max(1, ...nodeN);

  let svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + W + '" height="' + H + '" style="font-family:system-ui;max-width:100%">';
  svg += '<rect width="' + W + '" height="' + H + '" fill="' + (theme.surface || '#fff') + '"/>';

  // Draw edges
  for (const e of edges) {
    const p1 = positions[e.t1Idx], p2 = positions[e.t2Idx];
    const strokeW = Math.max(1.5, Math.min(10, e.nStudies * 2.5));
    svg += '<line x1="' + p1.x.toFixed(1) + '" y1="' + p1.y.toFixed(1) + '" x2="' + p2.x.toFixed(1) + '" y2="' + p2.y.toFixed(1) + '"' +
      ' stroke="' + (isDark ? '#64748b' : '#94a3b8') + '" stroke-width="' + strokeW.toFixed(1) + '" opacity="0.7"/>';
    // Edge label (number of studies)
    const mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2;
    svg += '<text x="' + mx.toFixed(1) + '" y="' + (my - 4).toFixed(1) + '" text-anchor="middle" font-size="10" fill="' + (theme.textMuted || '#6b7280') + '">' + e.nStudies + '</text>';
  }

  // Draw nodes
  for (let i = 0; i < nT; i++) {
    const r = 12 + 20 * nodeN[i] / maxN;
    const p = positions[i];
    svg += '<circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="' + r.toFixed(1) + '"' +
      ' fill="' + (isDark ? '#3b82f6' : '#2563eb') + '" opacity="0.85" stroke="#fff" stroke-width="2"/>';
    svg += '<text x="' + p.x.toFixed(1) + '" y="' + (p.y + r + 14).toFixed(1) + '" text-anchor="middle" font-size="11" font-weight="600" fill="' + (theme.text || '#1e293b') + '">' + escapeHtml(treatments[i]) + '</text>';
  }

  svg += '</svg>';
  return svg;
}

/** Render league table as HTML */
function renderLeagueTable(nmaResult) {
  const { treatments, leagueTable, nT, confLevel } = nmaResult;
  const confPct = Math.round(confLevel * 100);
  const lookup = new Map();
  for (const entry of leagueTable) {
    lookup.set(entry.t1 + '||' + entry.t2, entry);
  }

  let html = '<h3 style="font-size:0.95rem;margin-bottom:8px">League Table (' + confPct + '% CI)</h3>';
  html += '<div style="overflow-x:auto"><table style="font-size:0.78rem;border-collapse:collapse;text-align:center">';
  // Header row
  html += '<tr><th style="padding:6px;border:1px solid var(--border);background:#f1f5f9"></th>';
  for (const t of treatments) {
    html += '<th style="padding:6px;border:1px solid var(--border);background:#f1f5f9;font-size:0.72rem;max-width:80px;overflow:hidden;text-overflow:ellipsis" title="' + escapeHtml(t) + '">' + escapeHtml(t.length > 12 ? t.substring(0, 10) + '..' : t) + '</th>';
  }
  html += '</tr>';

  for (let i = 0; i < nT; i++) {
    html += '<tr>';
    html += '<th style="padding:6px;border:1px solid var(--border);background:#f1f5f9;text-align:left;font-size:0.72rem">' + escapeHtml(treatments[i]) + '</th>';
    for (let j = 0; j < nT; j++) {
      if (i === j) {
        html += '<td style="padding:6px;border:1px solid var(--border);background:#e2e8f0;font-weight:700">' + escapeHtml(treatments[i].length > 8 ? treatments[i].substring(0, 6) + '..' : treatments[i]) + '</td>';
      } else {
        const entry = lookup.get(treatments[i] + '||' + treatments[j]);
        if (entry) {
          const sig = (entry.lo > 0 || entry.hi < 0);
          const bg = sig ? (entry.effect > 0 ? 'background:rgba(16,185,129,0.15)' : 'background:rgba(239,68,68,0.15)') : '';
          html += '<td style="padding:4px 3px;border:1px solid var(--border);font-size:0.72rem;' + bg + '">' +
            entry.effect.toFixed(2) + '<br><span style="color:var(--text-muted);font-size:0.65rem">(' + entry.lo.toFixed(2) + ', ' + entry.hi.toFixed(2) + ')</span></td>';
        } else {
          html += '<td style="padding:4px;border:1px solid var(--border)">-</td>';
        }
      }
    }
    html += '</tr>';
  }
  html += '</table></div>';
  return html;
}

/** Render P-score / SUCRA bar chart as SVG */
function renderPScoreBars(treatments, scores, label) {
  const n = treatments.length;
  const sorted = treatments.map((t, i) => ({ t, s: scores[i] }))
    .sort((a, b) => b.s - a.s);

  const barH = 28, pad = 120;
  const W = 500, H = n * barH + 40;
  const maxBarW = W - pad - 40;
  const theme = getThemeColors();
  const isDark = document.body.classList.contains('dark-mode');

  let svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + W + '" height="' + H + '" style="font-family:system-ui;max-width:100%">';
  svg += '<rect width="' + W + '" height="' + H + '" fill="' + (theme.surface || '#fff') + '"/>';
  svg += '<text x="' + (W / 2) + '" y="18" text-anchor="middle" font-size="13" font-weight="600" fill="' + (theme.text || '#1e293b') + '">' + label + '</text>';

  for (let i = 0; i < n; i++) {
    const y = 30 + i * barH;
    const barW = sorted[i].s * maxBarW;
    const hue = sorted[i].s > 0.7 ? '142' : sorted[i].s > 0.4 ? '45' : '0';
    svg += '<text x="' + (pad - 4) + '" y="' + (y + barH / 2 + 4) + '" text-anchor="end" font-size="11" fill="' + (theme.text || '#1e293b') + '">' + escapeHtml(sorted[i].t) + '</text>';
    svg += '<rect x="' + pad + '" y="' + (y + 3) + '" width="' + barW.toFixed(1) + '" height="' + (barH - 6) + '" rx="3" fill="hsl(' + hue + ',70%,' + (isDark ? '45%' : '55%') + ')"/>';
    svg += '<text x="' + (pad + barW + 6) + '" y="' + (y + barH / 2 + 4) + '" font-size="11" fill="' + (theme.textMuted || '#6b7280') + '">' + (sorted[i].s * 100).toFixed(1) + '%</text>';
  }

  svg += '</svg>';
  return svg;
}

/** Render rank probability heatmap */
function renderRankProbHeatmap(treatments, rankProbs) {
  const nT = treatments.length;
  // Sort treatments by SUCRA (best first)
  const sucra = [];
  for (let t = 0; t < nT; t++) {
    let meanRank = 0;
    for (let r = 0; r < nT; r++) meanRank += rankProbs[t][r] * (r + 1);
    sucra.push((nT - meanRank) / (nT - 1));
  }
  const sorted = treatments.map((t, i) => ({ t, i, sucra: sucra[i] })).sort((a, b) => b.sucra - a.sucra);

  const cellW = 50, cellH = 28, labelW = 120, headerH = 30;
  const W = labelW + nT * cellW, H = headerH + nT * cellH;

  let html = '<h3 style="font-size:0.95rem;margin-bottom:8px">Rank Probability Heatmap</h3>';
  html += '<div style="overflow-x:auto"><table style="font-size:0.75rem;border-collapse:collapse">';
  html += '<tr><th style="padding:4px;border:1px solid var(--border)"></th>';
  for (let r = 0; r < nT; r++) {
    html += '<th style="padding:4px 8px;border:1px solid var(--border);background:#f1f5f9">Rank ' + (r + 1) + '</th>';
  }
  html += '</tr>';

  for (const { t, i } of sorted) {
    html += '<tr><td style="padding:4px 8px;border:1px solid var(--border);font-weight:600;white-space:nowrap">' + escapeHtml(t) + '</td>';
    for (let r = 0; r < nT; r++) {
      const prob = rankProbs[i][r];
      const intensity = Math.round(prob * 255);
      const bg = 'rgba(37,99,235,' + (prob * 0.8).toFixed(2) + ')';
      const color = prob > 0.4 ? '#fff' : 'var(--text)';
      html += '<td style="padding:4px 8px;border:1px solid var(--border);text-align:center;background:' + bg + ';color:' + color + '">' + (prob * 100).toFixed(0) + '%</td>';
    }
    html += '</tr>';
  }
  html += '</table></div>';
  return html;
}
```

---

## Task 12: Rewire runAnalysis() for NMA

**Files:**
- Modify: `metasprint-nma.html` lines ~8800–8910 (runAnalysis function)

**Step 1: Replace the two-stage dose mapping (lines 8807–8819)**

Remove the dose-response slope → effect mapping block entirely.

**Step 2: After validation gates pass (line ~8870), add NMA logic**

Replace the existing pooling call with:

```javascript
// Build network
const network = buildNetworkGraph(valid);
if (!network || network.nE === 0) {
  showToast('No valid pairwise comparisons found. Ensure Treatment 1 and Treatment 2 are filled.', 'warning');
  return;
}

// Populate reference treatment dropdown
const refSelect = document.getElementById('nmaRefSelect');
if (refSelect) {
  const currentVal = refSelect.value;
  refSelect.innerHTML = '<option value="auto">Auto (most connected)</option>';
  for (const t of network.treatments) {
    refSelect.innerHTML += '<option value="' + escapeHtml(t) + '"' + (t === currentVal ? ' selected' : '') + '>' + escapeHtml(t) + '</option>';
  }
}

// Check connectivity
if (network.components.length > 1) {
  const compSizes = network.components.map(c => c.length).sort((a, b) => b - a);
  warnMsgs.push('Disconnected network: ' + network.components.length + ' components (sizes: ' + compSizes.join(', ') + '). Only the largest component will be analyzed.');
}

// Run NMA
const nmaEngine = document.getElementById('nmaModelSelect')?.value || 'frequentist';
let nmaResult;
if (nmaEngine === 'bayesian') {
  showToast('Running Bayesian NMA (MCMC)... this may take a few seconds.', 'info');
  nmaResult = runBayesianNMA(network, confLevel);
} else {
  nmaResult = runFrequentistNMA(network, confLevel);
}

if (!nmaResult) {
  showToast('NMA failed. Check that the network has at least 2 treatments and 1 comparison.', 'warning');
  return;
}
lastAnalysisResult = nmaResult;

// Render network plot
const networkEl = document.getElementById('networkPlotContainer');
if (networkEl) networkEl.innerHTML = renderNetworkPlot(network);

// Render league table
const leagueEl = document.getElementById('leagueTableContainer');
if (leagueEl) leagueEl.innerHTML = renderLeagueTable(nmaResult);

// Render P-scores or SUCRA
const pscoreEl = document.getElementById('pscoreContainer');
if (pscoreEl) {
  if (nmaEngine === 'bayesian' && nmaResult.sucra) {
    pscoreEl.innerHTML = renderPScoreBars(nmaResult.treatments, nmaResult.sucra, 'SUCRA (Surface Under Cumulative Ranking)');
    // Also show rank probability heatmap
    const rankEl = document.getElementById('rankProbContainer');
    if (rankEl) rankEl.innerHTML = renderRankProbHeatmap(nmaResult.treatments, nmaResult.rankProbs);
  } else if (nmaResult.pscores) {
    pscoreEl.innerHTML = renderPScoreBars(nmaResult.treatments, nmaResult.pscores, 'P-scores (Frequentist Ranking)');
  }
}

// Run consistency test (node-splitting)
const consistencyEl = document.getElementById('consistencyContainer');
if (consistencyEl && nmaEngine === 'frequentist') {
  const nodeSplits = runNodeSplitting(network, confLevel);
  if (nodeSplits.length > 0) {
    // Render consistency forest
    let html = '<h3 style="font-size:0.95rem;margin-bottom:8px">Consistency Test (Node-Splitting)</h3>';
    html += '<table style="font-size:0.82rem;border-collapse:collapse;width:100%">';
    html += '<thead><tr style="border-bottom:2px solid var(--border)">' +
      '<th style="padding:6px;text-align:left">Comparison</th>' +
      '<th style="padding:6px;text-align:right">Direct</th>' +
      '<th style="padding:6px;text-align:right">Indirect</th>' +
      '<th style="padding:6px;text-align:right">Difference</th>' +
      '<th style="padding:6px;text-align:right">p-value</th>' +
      '<th style="padding:6px;text-align:center">Consistent?</th></tr></thead><tbody>';
    for (const ns of nodeSplits) {
      const color = ns.inconsistent ? 'color:#ef4444;font-weight:600' : '';
      html += '<tr style="border-bottom:1px solid var(--border)">' +
        '<td style="padding:5px">' + escapeHtml(ns.t1) + ' vs ' + escapeHtml(ns.t2) + '</td>' +
        '<td style="padding:5px;text-align:right">' + ns.directEffect.toFixed(3) + ' (SE ' + ns.directSE.toFixed(3) + ')</td>' +
        '<td style="padding:5px;text-align:right">' + ns.indirectEffect.toFixed(3) + ' (SE ' + ns.indirectSE.toFixed(3) + ')</td>' +
        '<td style="padding:5px;text-align:right">' + ns.diff.toFixed(3) + '</td>' +
        '<td style="padding:5px;text-align:right;' + color + '">' + (ns.pValue < 0.001 ? '<0.001' : ns.pValue.toFixed(3)) + '</td>' +
        '<td style="padding:5px;text-align:center">' + (ns.inconsistent ? 'No' : 'Yes') + '</td></tr>';
    }
    html += '</tbody></table>';
    consistencyEl.innerHTML = html;
  }
}

// Component NMA contribution matrix
const componentEl = document.getElementById('componentContainer');
if (componentEl && nmaEngine === 'frequentist' && nmaResult.hatMatrix) {
  const contrib = computeContributionMatrix(nmaResult);
  let html = '<h3 style="font-size:0.95rem;margin-bottom:8px">Evidence Contribution Matrix</h3>';
  html += '<div style="overflow-x:auto"><table style="font-size:0.72rem;border-collapse:collapse">';
  html += '<tr><th style="padding:4px;border:1px solid var(--border)">Network Est.</th>';
  for (const e of nmaResult.edges) {
    html += '<th style="padding:4px;border:1px solid var(--border);writing-mode:vertical-lr;font-size:0.65rem">' + escapeHtml(e.t1) + ' v ' + escapeHtml(e.t2) + '</th>';
  }
  html += '</tr>';
  for (let i = 0; i < nmaResult.nE; i++) {
    html += '<tr><td style="padding:4px;border:1px solid var(--border);white-space:nowrap">' + escapeHtml(nmaResult.edges[i].t1) + ' vs ' + escapeHtml(nmaResult.edges[i].t2) + '</td>';
    for (let j = 0; j < nmaResult.nE; j++) {
      const pct = contrib[i][j];
      const bg = 'rgba(37,99,235,' + (pct / 100 * 0.7).toFixed(2) + ')';
      const color = pct > 40 ? '#fff' : 'var(--text)';
      html += '<td style="padding:3px;border:1px solid var(--border);text-align:center;background:' + bg + ';color:' + color + '">' + (pct > 0.5 ? pct.toFixed(0) + '%' : '') + '</td>';
    }
    html += '</tr>';
  }
  html += '</table></div>';
  componentEl.innerHTML = html;
}
```

**Step 3: Update the summary HTML (lines 8888–8905)**

Replace dose-response interpretation with NMA interpretation:

```javascript
const favours = 'Network contains ' + network.nT + ' treatments and ' + network.nE + ' direct comparisons';
```

**Step 4: Also run pairwise forest plot for the reference comparison**

Keep the existing `renderForestPlot()` call but pass it the per-comparison studies for the most informative edge.

**Step 5: Remove the `renderDoseResponseAnalysis(studies, confLevel)` call at the end of runAnalysis()**

Delete any remaining call to `renderDoseResponseAnalysis`.

---

## Task 13: Update exportDoseResponseCSV() → exportNMACSV()

**Files:**
- Modify: `metasprint-nma.html` lines ~7074–7087

**Step 1: Rename and update columns**

```javascript
function exportNMACSV() {
  const rows = [['Study ID','Trial ID','NCT ID','PMID','DOI','Outcome','Timepoint','Population',
    'Treatment 1','Treatment 2','N1','N2','Effect','Lower CI','Upper CI','SE','Type','Subgroup','Notes']];
  for (const s of extractedStudies) {
    rows.push([s.authorYear, s.trialId, s.nctId, s.pmid, s.doi, s.outcomeId, s.timepoint,
      s.analysisPopulation, s.treatment1, s.treatment2, s.n1, s.n2,
      s.effectEstimate, s.lowerCI, s.upperCI, s.se, s.effectType, s.subgroup, s.notes]);
  }
  downloadCSV(rows, 'metasprint-nma-export.csv');
}
```

**Step 2: Add league table CSV export**

```javascript
function exportLeagueTableCSV() {
  if (!lastAnalysisResult?.leagueTable) { showToast('Run analysis first', 'warning'); return; }
  const rows = [['Treatment 1', 'Treatment 2', 'Effect', 'Lower CI', 'Upper CI', 'SE', 'p-value']];
  for (const entry of lastAnalysisResult.leagueTable) {
    rows.push([entry.t1, entry.t2, entry.effect?.toFixed(4), entry.lo?.toFixed(4), entry.hi?.toFixed(4), entry.se?.toFixed(4), entry.pValue?.toFixed(4)]);
  }
  downloadCSV(rows, 'nma-league-table.csv');
}
```

---

## Task 14: Update paper generation

**Files:**
- Modify: `metasprint-nma.html` lines ~15994–16250 (generatePaper function)

**Step 1: Replace dose-response methods text with NMA methods**

Find all references to "dose-response", "dose levels", "linear/quadratic/Emax model" in the paper generator and replace with:

- "Network meta-analysis was conducted using a graph-theoretic frequentist approach (Rucker 2012)"
- "Treatments were compared using a random-effects consistency model with DerSimonian-Laird tau-squared estimation"
- "Treatment ranking was assessed using P-scores (Rucker & Schwarzer 2015)"
- "Consistency was evaluated using node-splitting (Dias et al. 2010)"
- "Evidence contributions were quantified using the contribution matrix approach (Papakonstantinou et al. 2018)"

---

## Task 15: Final validation + div balance check

**Files:**
- Verify: `metasprint-nma.html`

**Step 1: Div balance check**

Run in browser console:
```javascript
const html = document.documentElement.outerHTML;
const opens = (html.match(/<div[\s>]/g) || []).length;
const closes = (html.match(/<\/div>/g) || []).length;
console.log('Opens:', opens, 'Closes:', closes, 'Balanced:', opens === closes);
```

**Step 2: No `</script>` in template literals**

Search for literal `</script>` inside JS template literals. Replace any with `${'<'}/script>`.

**Step 3: Function name uniqueness**

Search for duplicate `function xxx()` declarations. Ensure no dose-response ghosts remain.

**Step 4: Element ID uniqueness**

Verify no duplicate IDs (especially new ones like `networkPlotContainer`, `leagueTableContainer`).

**Step 5: localStorage key uniqueness**

Confirm all keys use `metaSprintNMA_` prefix, not the old `metaSprint_` prefix.

**Step 6: Browser smoke test**

1. Open `metasprint-nma.html` in Chrome
2. Create a new project
3. Add 3+ studies with Treatment 1/Treatment 2 fields
4. Run analysis — verify network plot, league table, P-scores render
5. Toggle Bayesian engine — verify SUCRA + rank heatmap render
6. Check consistency container renders
7. Export CSV — verify NMA columns
8. Dark mode toggle — verify all new visualizations
