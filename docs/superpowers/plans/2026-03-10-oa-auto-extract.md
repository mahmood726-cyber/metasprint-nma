# OA Auto-Extract Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an "Auto-Extract from OA Sources" button to MetaSprint NMA's Search phase that fetches structured results from CT.gov and parses PubMed abstracts to extract HR/OR/RR/MD effect sizes, then presents a review panel where users verify every number before committing to the Extract table.

**Architecture:** All code goes into the single file `metasprint-nma.html`. Three new JS functions: `runAutoExtract()` (orchestrator), `extractFromCTGov(nctId)` (CT.gov results parser), `parseAbstractEffects(abstractText)` (PubMed regex extractor). One new HTML section: the extraction review panel between `#searchStatus` and `#searchResults`. One new column in the Extract table: `source` badge. Smart merge prioritizes CT.gov over PubMed, provenance metadata stored per study row.

**Tech Stack:** Vanilla JS, CT.gov API v2, PubMed efetch XML, existing `rateLimitedFetch()`, existing `addStudyRow()`.

**Spec:** `docs/superpowers/specs/2026-03-10-oa-auto-extract-design.md`

---

## File Structure

Single file modified: `C:\Users\user\Downloads\metasprintnma\metasprint-nma.html`

Insertion points:
- **HTML** (~line 1264): Auto-extract button row + review panel div, between `#searchStatus` and `#searchResults`
- **CSS** (~line 500): Styles for review panel, source badges, evidence highlights
- **JS extraction engine** (~line 14990, after `searchAll()`): `runAutoExtract()`, `extractFromCTGov()`, `parseAbstractEffects()`, `renderExtractionReview()`, `acceptExtractedStudies()`
- **JS addStudyRow** (~line 7124): Add `extractionSource` and `extractionEvidence` fields
- **JS renderExtractTable** (find exact line): Add source badge column

Test file: `C:\Users\user\Downloads\metasprintnma\test_auto_extract.py` (new Selenium test)

---

## Chunk 1: PubMed Abstract Regex Engine + CT.gov Results Parser

### Task 1: Add PubMed abstract effect-size regex parser

**Files:**
- Modify: `metasprint-nma.html` (~line 14990, after `searchAll()` function ends)

- [ ] **Step 1: Write the `parseAbstractEffects` function**

Insert after the `searchAll` function (after line 14990). This function takes a PubMed abstract string and returns an array of extracted effects.

```js
// ============================================================
// OA AUTO-EXTRACT ENGINE
// ============================================================

/**
 * Parse effect sizes from a PubMed structured abstract.
 * Returns array of { effectType, estimate, lowerCI, upperCI, pValue, sourceSentence, matchSpan }
 */
function parseAbstractEffects(abstractText) {
  if (!abstractText || typeof abstractText !== 'string') return [];
  const results = [];
  const seen = new Set(); // deduplicate identical extractions

  // Split into sentences for provenance tracking
  const sentences = abstractText.split(/(?<=[.;])\s+/);

  // Effect patterns: HR, OR, RR, MD
  const patterns = [
    { type: 'HR', re: /\b(?:HR|hazard\s+ratio)\s*[=:,]?\s*(\d+\.?\d*)\s*[,;]?\s*(?:\(?95%?\s*CI\)?|CI)\s*[=:,]?\s*(\d+\.?\d*)\s*[-\u2013to]+\s*(\d+\.?\d*)/gi },
    { type: 'OR', re: /\b(?:OR|odds\s+ratio)\s*[=:,]?\s*(\d+\.?\d*)\s*[,;]?\s*(?:\(?95%?\s*CI\)?|CI)\s*[=:,]?\s*(\d+\.?\d*)\s*[-\u2013to]+\s*(\d+\.?\d*)/gi },
    { type: 'RR', re: /\b(?:RR|relative\s+risk|risk\s+ratio)\s*[=:,]?\s*(\d+\.?\d*)\s*[,;]?\s*(?:\(?95%?\s*CI\)?|CI)\s*[=:,]?\s*(\d+\.?\d*)\s*[-\u2013to]+\s*(\d+\.?\d*)/gi },
    { type: 'MD', re: /\b(?:mean\s+diff(?:erence)?|MD|difference\s+in\s+means?)\s*[=:,]?\s*(-?\d+\.?\d*)\s*[,;]?\s*(?:\(?95%?\s*CI\)?|CI)\s*[=:,]?\s*(-?\d+\.?\d*)\s*[-\u2013to]+\s*(-?\d+\.?\d*)/gi },
  ];

  // P-value pattern (standalone, matched to nearest preceding effect)
  const pRe = /[Pp]\s*([=<>])\s*(\d+\.?\d*(?:\s*[x\u00d7]\s*10\s*[-\u2013]\s*\d+)?)/g;

  for (const sent of sentences) {
    for (const pat of patterns) {
      pat.re.lastIndex = 0;
      let m;
      while ((m = pat.re.exec(sent)) !== null) {
        const est = parseFloat(m[1]);
        const lo = parseFloat(m[2]);
        const hi = parseFloat(m[3]);
        if (!isFinite(est) || !isFinite(lo) || !isFinite(hi)) continue;
        if (lo > hi) continue; // sanity
        const key = pat.type + ':' + est + ':' + lo + ':' + hi;
        if (seen.has(key)) continue;
        seen.add(key);

        // Try to find p-value in same sentence
        let pValue = null;
        pRe.lastIndex = 0;
        const pm = pRe.exec(sent);
        if (pm) {
          const pStr = pm[2].replace(/\s*[x\u00d7]\s*10\s*[-\u2013]\s*/, 'e-');
          pValue = parseFloat(pStr);
          if (!isFinite(pValue)) pValue = null;
        }

        results.push({
          effectType: pat.type,
          estimate: est,
          lowerCI: lo,
          upperCI: hi,
          pValue: pValue,
          sourceSentence: sent.trim(),
          matchSpan: [m.index, m.index + m[0].length]
        });
      }
    }
  }
  return results;
}
```

- [ ] **Step 2: Verify function loads without JS errors**

Open the HTML in Chrome, open DevTools console, type `parseAbstractEffects("HR 0.86, 95% CI 0.78-0.95, P=0.002")` and confirm it returns an array with one HR entry.

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add parseAbstractEffects regex engine for PubMed abstracts"
```

### Task 2: Add CT.gov results section parser

**Files:**
- Modify: `metasprint-nma.html` (insert after `parseAbstractEffects`)

- [ ] **Step 1: Write the `extractFromCTGov` function**

```js
/**
 * Fetch and parse CT.gov resultsSection for a given NCT ID.
 * Returns array of { outcomeTitle, effectType, estimate, lowerCI, upperCI, pValue, arms, fieldPath }
 */
async function extractFromCTGov(nctId) {
  if (!nctId || !/^NCT\d{8}$/i.test(nctId)) return [];
  try {
    const url = 'https://clinicaltrials.gov/api/v2/studies/' + nctId +
      '?fields=resultsSection,protocolSection.armsInterventionsModule';
    const resp = await rateLimitedFetch(url, 'ctgov');
    if (!resp.ok) return [];
    const study = await resp.json();
    const results = study.resultsSection;
    if (!results) return [];

    const extracted = [];

    // Parse outcome measures
    const outcomeMods = results.outcomeMeasuresModule?.outcomeMeasures || [];
    for (let oi = 0; oi < outcomeMods.length; oi++) {
      const om = outcomeMods[oi];
      const title = om.title || 'Outcome ' + (oi + 1);
      const analyses = om.analyses || [];

      for (let ai = 0; ai < analyses.length; ai++) {
        const an = analyses[ai];
        const paramType = (an.paramType || '').toLowerCase();
        const paramValue = parseFloat(an.paramValue);
        if (!isFinite(paramValue)) continue;

        // Determine effect type from paramType
        let effectType = null;
        if (paramType.includes('hazard')) effectType = 'HR';
        else if (paramType.includes('odds')) effectType = 'OR';
        else if (paramType.includes('risk ratio') || paramType.includes('relative risk')) effectType = 'RR';
        else if (paramType.includes('mean diff') || paramType.includes('difference')) effectType = 'MD';
        else if (paramType.includes('ratio')) effectType = 'OR'; // fallback for generic "ratio"
        if (!effectType) continue;

        // CI bounds
        const ciLower = parseFloat(an.ciLowerLimit);
        const ciUpper = parseFloat(an.ciUpperLimit);
        const pVal = an.pValue != null ? parseFloat(String(an.pValue).replace(/[<>]/g, '')) : null;

        // Arms
        const groupIds = an.groupIds || [];
        const armGroups = study.protocolSection?.armsInterventionsModule?.armGroups || [];
        const armLabels = groupIds.map(function(gid) {
          // Map group IDs like "OG000" to arm labels
          const idx = parseInt((gid.match(/\d+/) || ['0'])[0], 10);
          return armGroups[idx]?.label || gid;
        });

        extracted.push({
          outcomeTitle: title,
          effectType: effectType,
          estimate: paramValue,
          lowerCI: isFinite(ciLower) ? ciLower : null,
          upperCI: isFinite(ciUpper) ? ciUpper : null,
          pValue: isFinite(pVal) ? pVal : null,
          arms: armLabels,
          fieldPath: 'resultsSection.outcomeMeasures[' + oi + '].analyses[' + ai + ']'
        });
      }

      // Also extract group-level measures for continuous outcomes (mean/SD)
      const groups = om.groups || [];
      const measures = om.measures || [];
      for (const measure of measures) {
        const classes = measure.classes || [];
        for (const cls of classes) {
          const cats = cls.categories || [];
          for (const cat of cats) {
            const measurements = cat.measurements || [];
            // Check if this is mean/SD data we can convert to MD
            if (measurements.length >= 2 && measure.paramType === 'Mean') {
              const m0 = measurements[0], m1 = measurements[1];
              const val0 = parseFloat(m0.value), val1 = parseFloat(m1.value);
              const sd0 = parseFloat(m0.spread), sd1 = parseFloat(m1.spread);
              if (isFinite(val0) && isFinite(val1) && isFinite(sd0) && isFinite(sd1)) {
                const n0 = parseInt(m0.numAffected || m0.numAnalyzed, 10) || null;
                const n1 = parseInt(m1.numAffected || m1.numAnalyzed, 10) || null;
                extracted.push({
                  outcomeTitle: title + ' (arm-level means)',
                  effectType: 'MD_RAW',
                  estimate: null, // will be computed downstream
                  lowerCI: null,
                  upperCI: null,
                  pValue: null,
                  arms: [groups[0]?.title || 'Arm 1', groups[1]?.title || 'Arm 2'],
                  fieldPath: 'resultsSection.outcomeMeasures[' + oi + '].measures',
                  rawMeans: { mean1: val0, sd1: sd0, n1: n0, mean2: val1, sd2: sd1, n2: n1 }
                });
              }
            }
          }
        }
      }
    }

    return extracted;
  } catch (err) {
    msaLog('warn', 'autoExtract', 'CT.gov results fetch failed for ' + nctId + ': ' + (err?.message || err));
    return [];
  }
}
```

- [ ] **Step 2: Verify function loads without JS errors**

Open DevTools console, type `extractFromCTGov('NCT02540993').then(r => console.log(r))` (FIGARO-DKD). Confirm it returns extracted outcomes (may be empty if trial hasn't posted results yet, which is fine).

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add extractFromCTGov parser for CT.gov resultsSection"
```

### Task 3: Add PubMed abstract fetcher

**Files:**
- Modify: `metasprint-nma.html` (insert after `extractFromCTGov`)

- [ ] **Step 1: Write `fetchPubMedAbstract` function**

```js
/**
 * Fetch structured abstract from PubMed efetch for a given PMID.
 * Returns { abstract, title, authors, year, lang, isRetracted }
 */
async function fetchPubMedAbstract(pmid) {
  if (!pmid) return null;
  try {
    const url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=' +
      encodeURIComponent(pmid) + '&rettype=xml&retmode=text';
    const resp = await rateLimitedFetch(url, 'pubmed');
    if (!resp.ok) return null;
    const xml = await resp.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(xml, 'text/xml');

    // Extract structured abstract
    const abstractParts = doc.querySelectorAll('AbstractText');
    let abstractText = '';
    let resultsText = '';
    for (const part of abstractParts) {
      const label = part.getAttribute('NlmCategory') || part.getAttribute('Label') || '';
      const text = part.textContent || '';
      abstractText += text + ' ';
      if (label.toUpperCase() === 'RESULTS' || label.toUpperCase() === 'FINDINGS') {
        resultsText += text + ' ';
      }
    }
    // If no structured labels, use full abstract
    if (!resultsText) resultsText = abstractText;

    // Check retraction
    const pubStatuses = doc.querySelectorAll('PublicationStatus');
    const commentsCorrections = doc.querySelectorAll('CommentsCorrections');
    let isRetracted = false;
    for (const cc of commentsCorrections) {
      if ((cc.getAttribute('RefType') || '').toLowerCase().includes('retract')) {
        isRetracted = true;
      }
    }

    // Language
    const langEl = doc.querySelector('Language');
    const lang = langEl ? langEl.textContent : 'eng';

    // Title, authors, year
    const titleEl = doc.querySelector('ArticleTitle');
    const yearEl = doc.querySelector('PubDate Year') || doc.querySelector('PubDate MedlineDate');
    const authorEls = doc.querySelectorAll('Author');
    const firstAuthor = authorEls.length > 0 ?
      ((authorEls[0].querySelector('LastName')?.textContent || '') + ' ' +
       (authorEls[0].querySelector('Initials')?.textContent || '')).trim() : '';
    const year = yearEl ? (yearEl.textContent || '').slice(0, 4) : '';

    return {
      abstract: resultsText.trim() || abstractText.trim(),
      fullAbstract: abstractText.trim(),
      title: titleEl ? titleEl.textContent : '',
      authors: firstAuthor,
      year: year,
      lang: lang,
      isRetracted: isRetracted
    };
  } catch (err) {
    msaLog('warn', 'autoExtract', 'PubMed abstract fetch failed for PMID ' + pmid + ': ' + (err?.message || err));
    return null;
  }
}
```

- [ ] **Step 2: Verify function loads**

Console test: `fetchPubMedAbstract('33264825').then(r => console.log(r))` (FIDELIO-DKD). Confirm it returns abstract text containing "hazard ratio".

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add fetchPubMedAbstract for PubMed efetch XML parsing"
```

---

## Chunk 2: Orchestrator + Smart Merge + HTML UI

### Task 4: Add HTML for auto-extract button and review panel

**Files:**
- Modify: `metasprint-nma.html` (~line 1264, between `#searchStatus` and `#searchResults`)

- [ ] **Step 1: Insert HTML for auto-extract row and review panel**

Insert between `<div id="searchStatus" ...></div>` (line 1264) and `<div id="searchResults"></div>` (line 1265):

```html
      <div id="autoExtractRow" style="display:none;margin:10px 0;padding:10px;background:var(--bg-alt);border:1px solid var(--border);border-radius:8px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <button id="autoExtractBtn" class="btn-success" onclick="runAutoExtract()" aria-label="Auto-extract effect sizes from open-access sources">Auto-Extract from OA Sources</button>
          <span id="autoExtractStatus" class="text-muted" style="font-size:0.82rem" role="status" aria-live="polite"></span>
          <span id="autoExtractCount" class="text-muted" style="font-size:0.78rem"></span>
        </div>
        <p class="text-muted" style="font-size:0.72rem;margin-top:4px">Extracts HR/OR/RR/MD from CT.gov results sections and PubMed structured abstracts. Every number shown with source evidence for verification.</p>
      </div>
      <div id="extractionReviewPanel" style="display:none;margin:10px 0;border:1px solid var(--border);border-radius:8px;background:var(--surface);max-height:70vh;overflow-y:auto" role="region" aria-label="Extraction review panel"></div>
```

- [ ] **Step 2: Add CSS for source badges and evidence highlights**

Insert in the `<style>` block (around line 500, among the existing badge styles):

```css
.source-badge { font-size: 0.68rem; padding: 1px 6px; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
.source-badge.ctgov { background: #065f46; color: #6ee7b7; }
.source-badge.pubmed { background: #1e3a5f; color: #93c5fd; }
.source-badge.both { background: #78350f; color: #fbbf24; }
.source-badge.manual { background: #334155; color: #94a3b8; }
.evidence-text { font-size: 0.75rem; color: var(--text-muted); font-family: monospace; background: var(--bg-alt); padding: 4px 8px; border-radius: 4px; margin-top: 4px; line-height: 1.4; max-height: 80px; overflow-y: auto; }
.evidence-highlight { background: rgba(251, 191, 36, 0.35); color: #fbbf24; font-weight: 700; padding: 0 2px; border-radius: 2px; }
.extract-review-trial { border-bottom: 1px solid var(--border); padding: 10px 14px; }
.extract-review-trial:last-child { border-bottom: none; }
.extract-review-outcome { margin: 6px 0 6px 20px; padding: 8px 10px; background: var(--bg-alt); border-radius: 6px; border-left: 3px solid var(--primary); }
.extract-review-outcome.pubmed-only { border-left-color: #3b82f6; }
.extract-review-value { font-weight: 700; font-size: 0.95rem; }
.extract-review-value input { width: 70px; font-size: 0.85rem; padding: 2px 4px; border: 1px solid var(--border); border-radius: 3px; background: var(--surface); color: var(--text); text-align: center; }
```

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add HTML/CSS for auto-extract button and review panel"
```

### Task 5: Add orchestrator function `runAutoExtract()`

**Files:**
- Modify: `metasprint-nma.html` (insert after the functions from Tasks 1-3)

- [ ] **Step 1: Write the orchestrator**

```js
let _autoExtractRunning = false;
let _extractionResults = []; // holds merged results for review panel

async function runAutoExtract() {
  if (_autoExtractRunning) return;
  if (!searchResultsCache || searchResultsCache.length === 0) {
    showToast('Run a search first', 'warning');
    return;
  }
  _autoExtractRunning = true;
  const statusEl = document.getElementById('autoExtractStatus');
  const btn = document.getElementById('autoExtractBtn');
  btn.disabled = true;
  _extractionResults = [];

  try {
    // Collect NCT IDs and PMIDs from search results
    const trials = [];
    for (const r of searchResultsCache) {
      const nctId = (r.nctId || '').toUpperCase();
      const pmid = r.pmid || '';
      const title = r.title || '';
      const authors = r.authors || '';
      const year = r.year || '';
      // Only process records that have an NCT ID or PMID
      if (nctId || pmid) {
        trials.push({ nctId, pmid, title, authors, year, doi: r.doi || '' });
      }
    }

    if (trials.length === 0) {
      showToast('No trials with NCT IDs or PMIDs found in search results', 'warning');
      return;
    }

    statusEl.textContent = 'Extracting from ' + trials.length + ' trials...';
    let ctgovCount = 0, pubmedCount = 0, noDataCount = 0;

    for (let i = 0; i < trials.length; i++) {
      const t = trials[i];
      statusEl.textContent = 'Processing ' + (i + 1) + '/' + trials.length + ': ' + (t.nctId || 'PMID:' + t.pmid) + '...';

      const trialResult = {
        nctId: t.nctId,
        pmid: t.pmid,
        title: t.title,
        authorYear: (t.authors.split(/[,;]/)[0] || '').trim() + (t.year ? ' ' + t.year : ''),
        doi: t.doi,
        outcomes: [], // merged outcomes
        ctgovRaw: [],
        pubmedRaw: [],
        source: 'none'
      };

      // 1. Try CT.gov results
      if (t.nctId) {
        const ctResults = await extractFromCTGov(t.nctId);
        trialResult.ctgovRaw = ctResults;
        if (ctResults.length > 0) ctgovCount++;
      }

      // 2. Try PubMed abstract
      if (t.pmid) {
        const pubData = await fetchPubMedAbstract(t.pmid);
        if (pubData && pubData.lang === 'eng' && !pubData.isRetracted) {
          const pubResults = parseAbstractEffects(pubData.abstract);
          trialResult.pubmedRaw = pubResults.map(function(pr) {
            pr.pmid = t.pmid;
            return pr;
          });
          if (pubResults.length > 0) pubmedCount++;
          // Update author/year from PubMed if better
          if (pubData.authors && !trialResult.authorYear) {
            trialResult.authorYear = pubData.authors + (pubData.year ? ' ' + pubData.year : '');
          }
          if (pubData.isRetracted) {
            trialResult.retracted = true;
          }
        }
      }

      // 3. Smart merge: CT.gov primary, PubMed fills gaps
      const merged = smartMergeOutcomes(trialResult.ctgovRaw, trialResult.pubmedRaw);
      trialResult.outcomes = merged;
      trialResult.source = trialResult.ctgovRaw.length > 0 && trialResult.pubmedRaw.length > 0 ? 'both' :
        trialResult.ctgovRaw.length > 0 ? 'ctgov' : trialResult.pubmedRaw.length > 0 ? 'pubmed' : 'none';

      if (merged.length === 0) noDataCount++;

      _extractionResults.push(trialResult);
    }

    statusEl.textContent = trials.length + ' trials processed: ' +
      ctgovCount + ' CT.gov, ' + pubmedCount + ' PubMed, ' + noDataCount + ' no data';

    // Render review panel
    renderExtractionReview();

  } catch (err) {
    showToast('Auto-extract error: ' + (err?.message || err), 'danger');
    statusEl.textContent = 'Error: ' + (err?.message || err);
  } finally {
    _autoExtractRunning = false;
    btn.disabled = false;
  }
}

/**
 * Smart merge: CT.gov outcomes are primary. PubMed outcomes only included
 * if no matching CT.gov outcome exists (by effect type + fuzzy outcome name).
 */
function smartMergeOutcomes(ctgovResults, pubmedResults) {
  const merged = [];

  // Add all CT.gov results first
  for (const ct of ctgovResults) {
    if (ct.effectType === 'MD_RAW') {
      // Raw means — include for review but flag as needing computation
      merged.push({
        effectType: 'MD',
        estimate: ct.rawMeans ? (ct.rawMeans.mean1 - ct.rawMeans.mean2) : null,
        lowerCI: null,
        upperCI: null,
        pValue: ct.pValue,
        outcomeTitle: ct.outcomeTitle,
        source: 'ctgov',
        evidence: { ctgov: { fieldPath: ct.fieldPath, rawMeans: ct.rawMeans } },
        arms: ct.arms,
        rawMeans: ct.rawMeans,
        checked: true
      });
    } else {
      merged.push({
        effectType: ct.effectType,
        estimate: ct.estimate,
        lowerCI: ct.lowerCI,
        upperCI: ct.upperCI,
        pValue: ct.pValue,
        outcomeTitle: ct.outcomeTitle,
        source: 'ctgov',
        evidence: { ctgov: { fieldPath: ct.fieldPath } },
        arms: ct.arms,
        checked: true
      });
    }
  }

  // Add PubMed results only if no CT.gov match exists
  for (const pm of pubmedResults) {
    const hasCTMatch = ctgovResults.some(function(ct) {
      return ct.effectType === pm.effectType &&
        Math.abs((ct.estimate || 0) - pm.estimate) < 0.05;
    });
    merged.push({
      effectType: pm.effectType,
      estimate: pm.estimate,
      lowerCI: pm.lowerCI,
      upperCI: pm.upperCI,
      pValue: pm.pValue,
      outcomeTitle: pm.effectType + ' outcome',
      source: hasCTMatch ? 'both' : 'pubmed',
      evidence: {
        pubmed: { pmid: pm.pmid, sentence: pm.sourceSentence, matchSpan: pm.matchSpan },
        ctgov: hasCTMatch ? merged.find(function(m) { return m.effectType === pm.effectType; })?.evidence.ctgov : null
      },
      checked: !hasCTMatch // auto-check PubMed-only; CT.gov-confirmed duplicates unchecked
    });
  }

  return merged;
}
```

- [ ] **Step 2: Verify orchestrator loads**

Console test: ensure `runAutoExtract` is defined (`typeof runAutoExtract` returns `"function"`).

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add runAutoExtract orchestrator with smart merge"
```

### Task 6: Add review panel renderer and accept function

**Files:**
- Modify: `metasprint-nma.html` (insert after Task 5 functions)

- [ ] **Step 1: Write `renderExtractionReview` and `acceptExtractedStudies`**

```js
function renderExtractionReview() {
  const panel = document.getElementById('extractionReviewPanel');
  if (!panel) return;

  const trialsWithData = _extractionResults.filter(function(t) { return t.outcomes.length > 0; });
  const totalOutcomes = trialsWithData.reduce(function(s, t) { return s + t.outcomes.length; }, 0);

  let html = '<div style="padding:10px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;flex-wrap:wrap;position:sticky;top:0;background:var(--surface);z-index:2">' +
    '<strong>Extraction Review</strong>' +
    '<span class="text-muted" style="font-size:0.82rem">' +
      _extractionResults.length + ' trials searched &middot; ' +
      trialsWithData.length + ' with results &middot; ' +
      totalOutcomes + ' effect sizes' +
    '</span>' +
    '<div style="margin-left:auto;display:flex;gap:6px">' +
      '<button class="btn-success btn-sm" onclick="acceptExtractedStudies()">Accept Selected &rarr; Extract Table</button>' +
      '<button class="btn-outline btn-sm" onclick="exportEvidenceCSV()">Export Evidence CSV</button>' +
      '<button class="btn-outline btn-sm" onclick="document.getElementById(\'extractionReviewPanel\').style.display=\'none\'">Close</button>' +
    '</div>' +
  '</div>';

  for (let ti = 0; ti < _extractionResults.length; ti++) {
    var t = _extractionResults[ti];
    var hasBadge = t.source !== 'none';
    var badgeClass = t.source === 'both' ? 'both' : t.source === 'ctgov' ? 'ctgov' : t.source === 'pubmed' ? 'pubmed' : '';

    html += '<div class="extract-review-trial">' +
      '<label style="display:flex;align-items:center;gap:8px;cursor:pointer">' +
        '<input type="checkbox" data-trial-idx="' + ti + '" ' + (t.outcomes.length > 0 ? 'checked' : '') +
        ' onchange="toggleExtractionTrial(' + ti + ',this.checked)">' +
        '<strong>' + escapeHtml(t.nctId || 'PMID:' + t.pmid) + '</strong> &mdash; ' +
        escapeHtml(t.authorYear || t.title.slice(0, 60)) +
        (hasBadge ? ' <span class="source-badge ' + badgeClass + '">' + escapeHtml(t.source) + '</span>' : '') +
        (t.retracted ? ' <span style="color:#ef4444;font-weight:700">RETRACTED</span>' : '') +
      '</label>';

    if (t.outcomes.length === 0) {
      html += '<div class="text-muted" style="margin-left:28px;font-size:0.82rem">No extractable data found</div>';
    }

    for (let oi = 0; oi < t.outcomes.length; oi++) {
      var o = t.outcomes[oi];
      var isPubmedOnly = o.source === 'pubmed';
      html += '<div class="extract-review-outcome' + (isPubmedOnly ? ' pubmed-only' : '') + '">' +
        '<label style="display:flex;align-items:center;gap:6px">' +
          '<input type="checkbox" data-trial-idx="' + ti + '" data-outcome-idx="' + oi + '" ' +
          (o.checked ? 'checked' : '') +
          ' onchange="_extractionResults[' + ti + '].outcomes[' + oi + '].checked=this.checked">' +
          '<span class="source-badge ' + (o.source === 'both' ? 'both' : o.source) + '" style="font-size:0.6rem">' + escapeHtml(o.source) + '</span>' +
          '<span style="font-size:0.82rem;color:var(--text-muted)">' + escapeHtml(o.outcomeTitle) + '</span>' +
        '</label>' +
        '<div class="extract-review-value" style="margin:4px 0 4px 28px">' +
          escapeHtml(o.effectType) + ' = ' +
          '<input type="number" step="any" value="' + (o.estimate ?? '') + '" onchange="_extractionResults[' + ti + '].outcomes[' + oi + '].estimate=parseFloat(this.value)">' +
          ' 95% CI [' +
          '<input type="number" step="any" value="' + (o.lowerCI ?? '') + '" onchange="_extractionResults[' + ti + '].outcomes[' + oi + '].lowerCI=parseFloat(this.value)">' +
          ', ' +
          '<input type="number" step="any" value="' + (o.upperCI ?? '') + '" onchange="_extractionResults[' + ti + '].outcomes[' + oi + '].upperCI=parseFloat(this.value)">' +
          ']' +
          (o.pValue != null ? ' p=' + o.pValue : '') +
        '</div>';

      // Evidence trail
      if (o.evidence) {
        html += '<div class="evidence-text">';
        if (o.evidence.ctgov) {
          html += '<strong>CT.gov:</strong> ' + escapeHtml(o.evidence.ctgov.fieldPath || '');
          if (o.evidence.ctgov.rawMeans) {
            var rm = o.evidence.ctgov.rawMeans;
            html += ' (mean1=' + rm.mean1 + ' SD=' + rm.sd1 + ' n=' + rm.n1 +
              '; mean2=' + rm.mean2 + ' SD=' + rm.sd2 + ' n=' + rm.n2 + ')';
          }
          html += '<br>';
        }
        if (o.evidence.pubmed) {
          var sent = o.evidence.pubmed.sentence || '';
          var span = o.evidence.pubmed.matchSpan;
          var highlighted = sent;
          if (span && span[0] != null && span[1] != null) {
            highlighted = escapeHtml(sent.slice(0, span[0])) +
              '<span class="evidence-highlight">' + escapeHtml(sent.slice(span[0], span[1])) + '</span>' +
              escapeHtml(sent.slice(span[1]));
          } else {
            highlighted = escapeHtml(sent);
          }
          html += '<strong>PubMed ' + escapeHtml(o.evidence.pubmed.pmid || '') + ':</strong> ' + highlighted;
        }
        html += '</div>';
      }

      html += '</div>'; // outcome
    }
    html += '</div>'; // trial
  }

  panel.innerHTML = html;
  panel.style.display = 'block';
}

function toggleExtractionTrial(trialIdx, checked) {
  var t = _extractionResults[trialIdx];
  if (!t) return;
  for (var i = 0; i < t.outcomes.length; i++) {
    t.outcomes[i].checked = checked;
  }
  // Update outcome checkboxes in DOM
  var boxes = document.querySelectorAll('input[data-trial-idx="' + trialIdx + '"][data-outcome-idx]');
  for (var b of boxes) b.checked = checked;
}

function acceptExtractedStudies() {
  var accepted = 0;
  for (var t of _extractionResults) {
    for (var o of t.outcomes) {
      if (!o.checked) continue;
      if (o.estimate == null && !o.rawMeans) continue;

      var data = {
        authorYear: t.authorYear || '',
        trialId: t.nctId || (t.pmid ? 'PMID:' + t.pmid : ''),
        nctId: t.nctId || '',
        pmid: t.pmid || '',
        doi: t.doi || '',
        outcomeId: o.outcomeTitle || 'primary outcome',
        effectEstimate: o.estimate,
        lowerCI: o.lowerCI,
        upperCI: o.upperCI,
        pValue: o.pValue,
        effectType: o.effectType,
        treatment1: (o.arms && o.arms[0]) ? o.arms[0] : '',
        treatment2: (o.arms && o.arms[1]) ? o.arms[1] : '',
        notes: '[Auto-extracted: ' + o.source + ']',
        extractionSource: o.source,
        extractionEvidence: o.evidence
      };

      // If raw means available, populate arm-level fields
      if (o.rawMeans) {
        data.mean1 = o.rawMeans.mean1;
        data.sd1 = o.rawMeans.sd1;
        data.nArm1 = o.rawMeans.n1;
        data.mean2 = o.rawMeans.mean2;
        data.sd2 = o.rawMeans.sd2;
        data.nArm2 = o.rawMeans.n2;
      }

      addStudyRow(data);
      accepted++;
    }
  }

  if (accepted > 0) {
    showToast(accepted + ' effect sizes added to Extract table', 'success');
    // Hide review panel
    document.getElementById('extractionReviewPanel').style.display = 'none';
    // Switch to Extract phase so user can see results
    switchPhase('extract');
  } else {
    showToast('No outcomes selected', 'warning');
  }
}

function exportEvidenceCSV() {
  var rows = ['Trial,NCT_ID,PMID,Outcome,Effect_Type,Estimate,Lower_CI,Upper_CI,P_Value,Source,CT.gov_Field,PubMed_Sentence'];
  for (var t of _extractionResults) {
    for (var o of t.outcomes) {
      rows.push([
        t.authorYear, t.nctId, t.pmid, o.outcomeTitle, o.effectType,
        o.estimate ?? '', o.lowerCI ?? '', o.upperCI ?? '', o.pValue ?? '',
        o.source,
        o.evidence?.ctgov?.fieldPath || '',
        '"' + (o.evidence?.pubmed?.sentence || '').replace(/"/g, '""') + '"'
      ].join(','));
    }
  }
  downloadFile(rows.join('\n'), 'extraction-evidence.csv', 'text/csv');
  showToast('Evidence CSV exported', 'success');
}
```

- [ ] **Step 2: Verify review panel renders**

Console test with mock data:
```js
_extractionResults = [{nctId:'NCT00000001',pmid:'12345',title:'Test',authorYear:'Test 2024',doi:'',outcomes:[{effectType:'HR',estimate:0.86,lowerCI:0.78,upperCI:0.95,pValue:0.002,outcomeTitle:'MACE',source:'pubmed',evidence:{pubmed:{pmid:'12345',sentence:'HR 0.86, 95% CI 0.78-0.95, P=0.002',matchSpan:[0,30]}},checked:true}],source:'pubmed'}];
renderExtractionReview();
```
Confirm the review panel appears with the trial, outcome, and highlighted evidence.

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add extraction review panel with evidence display and accept flow"
```

### Task 7: Wire auto-extract button visibility to search completion

**Files:**
- Modify: `metasprint-nma.html` (line ~14984 inside `searchAll()`)

- [ ] **Step 1: Show auto-extract row after search completes**

Find the line in `searchAll()` that says `showToast('All ' + sourceCount + ' sources searched...')` (around line 14984). Immediately after it, add:

```js
    // Show auto-extract button if we have results
    var aeRow = document.getElementById('autoExtractRow');
    if (aeRow && searchResultsCache.length > 0) {
      var nctCount = searchResultsCache.filter(function(r) { return r.nctId; }).length;
      var pmidCount = searchResultsCache.filter(function(r) { return r.pmid; }).length;
      aeRow.style.display = 'block';
      document.getElementById('autoExtractCount').textContent =
        nctCount + ' with NCT IDs, ' + pmidCount + ' with PMIDs';
    }
```

- [ ] **Step 2: Verify button appears after search**

Run a search for "finerenone" in the app. Confirm the "Auto-Extract from OA Sources" button appears below the search status.

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: show auto-extract button after search completes"
```

### Task 8: Add `extractionSource` field to study data model

**Files:**
- Modify: `metasprint-nma.html` (~line 7124, in `addStudyRow`)

- [ ] **Step 1: Add extraction provenance fields to study object**

Find the line `rob: { d1: '', d2: '', d3: '', d4: '', d5: '', overall: '' }` in `addStudyRow` (line 7124). After it, add:

```js
      extractionSource: data.extractionSource || 'manual',
      extractionEvidence: data.extractionEvidence || null
```

(Don't forget the comma after the `rob` line.)

- [ ] **Step 2: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add extractionSource/extractionEvidence to study data model"
```

---

## Chunk 3: Source Badge in Extract Table + Selenium Tests

### Task 9: Add source badge column to Extract table

**Files:**
- Modify: `metasprint-nma.html` (find `renderExtractTable` or equivalent table renderer)

- [ ] **Step 1: Find the extract table renderer**

Search for the function that builds the extract table rows (look for `renderExtractTable` or the function that iterates `extractedStudies` to build `<tr>` elements). Add a source badge cell after the author/year column:

```js
// Inside the row-building loop, after the authorYear cell:
'<td><span class="source-badge ' + (s.extractionSource || 'manual') + '">' +
  escapeHtml(s.extractionSource || 'manual') + '</span></td>' +
```

And add the corresponding `<th>Source</th>` to the header row.

- [ ] **Step 2: Verify badge appears**

Add a study via auto-extract, switch to Extract tab, confirm the source badge column shows "ctgov" / "pubmed" / "manual".

- [ ] **Step 3: Commit**

```bash
git add metasprint-nma.html
git commit -m "feat: add source badge column to Extract table"
```

### Task 10: Write Selenium test for auto-extract flow

**Files:**
- Create: `test_auto_extract.py`

- [ ] **Step 1: Write end-to-end Selenium test**

```python
"""
Selenium test for OA Auto-Extract feature.
Tests: search -> auto-extract button appears -> click -> review panel -> accept -> extract table populated.
"""
import io, sys, os, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metasprint-nma.html')
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')
TIMEOUT = 30
PASS = 0
FAIL = 0

def log_result(name, passed, detail=''):
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f'  [PASS] {name}' + (f' -- {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'  [FAIL] {name}' + (f' -- {detail}' if detail else ''))

def main():
    global PASS, FAIL
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1600,1200')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(3)

    try:
        driver.get(FILE_URL)
        WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
        time.sleep(1)
        # Dismiss onboarding
        try:
            driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except Exception:
            pass

        print('\n=== TEST: parseAbstractEffects ===')
        # Unit test the regex parser via JS
        result = driver.execute_script("""
            var r = parseAbstractEffects('The hazard ratio was HR 0.86, 95% CI 0.78-0.95, P=0.002. OR was 1.25 (95% CI 1.05 to 1.50).');
            return JSON.stringify(r);
        """)
        parsed = json.loads(result)
        log_result('AE-1: parseAbstractEffects returns results', len(parsed) >= 2, f'found {len(parsed)} effects')
        hr = next((p for p in parsed if p['effectType'] == 'HR'), None)
        log_result('AE-2: HR extracted correctly', hr and hr['estimate'] == 0.86, f'HR={hr}')
        log_result('AE-3: HR CI correct', hr and hr['lowerCI'] == 0.78 and hr['upperCI'] == 0.95)
        log_result('AE-4: HR p-value extracted', hr and hr['pValue'] == 0.002)
        orr = next((p for p in parsed if p['effectType'] == 'OR'), None)
        log_result('AE-5: OR extracted correctly', orr and orr['estimate'] == 1.25, f'OR={orr}')

        print('\n=== TEST: Edge cases ===')
        # Empty input
        empty = driver.execute_script("return parseAbstractEffects('').length")
        log_result('AE-6: Empty input returns 0', empty == 0)
        # No effect sizes
        none = driver.execute_script("return parseAbstractEffects('This is a study about diabetes.').length")
        log_result('AE-7: No-effect text returns 0', none == 0)
        # MD extraction
        md = driver.execute_script("""
            var r = parseAbstractEffects('Mean difference MD -3.5, 95% CI -5.2 to -1.8, p<0.001');
            return JSON.stringify(r);
        """)
        mdp = json.loads(md)
        log_result('AE-8: MD extracted', len(mdp) >= 1 and mdp[0]['effectType'] == 'MD', f'MD={mdp}')

        print('\n=== TEST: Auto-extract UI ===')
        # Check button exists but hidden
        ae_row = driver.execute_script("return document.getElementById('autoExtractRow')?.style.display")
        log_result('AE-9: Auto-extract row initially hidden', ae_row == 'none')

        # Check review panel exists but hidden
        rp = driver.execute_script("return document.getElementById('extractionReviewPanel')?.style.display")
        log_result('AE-10: Review panel initially hidden', rp == 'none')

        # Test renderExtractionReview with mock data
        driver.execute_script("""
            _extractionResults = [{
                nctId: 'NCT99999999', pmid: '12345678', title: 'Mock Trial',
                authorYear: 'TestAuthor 2024', doi: '', source: 'pubmed',
                outcomes: [{
                    effectType: 'HR', estimate: 0.75, lowerCI: 0.60, upperCI: 0.93,
                    pValue: 0.01, outcomeTitle: 'Primary MACE', source: 'pubmed',
                    evidence: { pubmed: { pmid: '12345678', sentence: 'HR 0.75, 95% CI 0.60-0.93', matchSpan: [0, 28] } },
                    checked: true
                }]
            }];
            renderExtractionReview();
        """)
        time.sleep(0.5)
        rp_vis = driver.execute_script("return document.getElementById('extractionReviewPanel')?.style.display")
        log_result('AE-11: Review panel visible after render', rp_vis == 'block')

        # Check evidence text is displayed
        ev = driver.execute_script("return document.querySelector('.evidence-text')?.textContent || ''")
        log_result('AE-12: Evidence text displayed', 'HR 0.75' in ev, f'evidence={ev[:80]}')

        # Accept and verify study added
        before = driver.execute_script("return extractedStudies?.length || 0")
        driver.execute_script("acceptExtractedStudies()")
        time.sleep(0.5)
        after = driver.execute_script("return extractedStudies?.length || 0")
        log_result('AE-13: Accept adds study to extract table', after == before + 1, f'{before} -> {after}')

        # Verify source field
        src = driver.execute_script("return extractedStudies[extractedStudies.length-1]?.extractionSource || ''")
        log_result('AE-14: extractionSource set correctly', src == 'pubmed', f'source={src}')

        print('\n=== TEST: Console Errors ===')
        logs = driver.get_log('browser')
        severe = [l for l in logs if l.get('level') == 'SEVERE']
        log_result('AE-15: No SEVERE console errors', len(severe) == 0, f'{len(severe)} errors')

    except Exception as e:
        print(f'\nFATAL: {e}')
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

    total = PASS + FAIL
    print(f'\n{"="*60}')
    print(f'RESULTS: {PASS} passed, {FAIL} failed / {total} total')
    print(f'{"="*60}')
    return FAIL

if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Run tests**

```bash
python test_auto_extract.py
```

Expected: 15/15 PASS

- [ ] **Step 3: Run existing test suite to verify no regressions**

```bash
python test_nma_comprehensive.py
```

Expected: 325/325 PASS

- [ ] **Step 4: Commit**

```bash
git add test_auto_extract.py metasprint-nma.html
git commit -m "test: add Selenium tests for OA auto-extract feature"
```

---

## Chunk 4: Final Integration + Safety Checks

### Task 11: Post-integration safety checks

- [ ] **Step 1: Verify div balance**

```bash
grep -cP '<div[\s>]' metasprint-nma.html && grep -cP '</div>' metasprint-nma.html
```

The delta should be unchanged from before (no structural HTML changes break balance).

- [ ] **Step 2: Verify no literal `</script>` in JS**

```bash
grep -n '</script>' metasprint-nma.html | grep -v '^\s*</script>'
```

Should return 0 matches inside `<script>` blocks.

- [ ] **Step 3: Run full test suite**

```bash
python test_nma_comprehensive.py
python test_auto_extract.py
```

Expected: 325/325 + 15/15 = 340 total, 0 failures.

- [ ] **Step 4: Manual smoke test**

1. Open metasprint-nma.html in browser
2. Go to Search phase
3. Enter "finerenone" in Population field
4. Click "Search All Sources"
5. Wait for search to complete
6. Verify "Auto-Extract from OA Sources" button appears
7. Click it
8. Verify review panel shows trials with evidence trails
9. Check a few outcomes, click "Accept Selected -> Extract Table"
10. Verify Extract table has new rows with source badges
11. Click Analyze — verify analysis runs on extracted data

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: OA auto-extract complete — CT.gov + PubMed -> review panel -> extract table"
```
