# OA Auto-Extract for MetaSprint NMA

**Date:** 2026-03-10
**Status:** Approved
**Scope:** Add auto-extraction of effect sizes from ClinicalTrials.gov structured results and PubMed structured abstracts into MetaSprint NMA's existing Search phase.

---

## Problem

Users must currently enter study data manually into the Extract table. For open-access sources (CT.gov results, PubMed abstracts), this data is machine-readable and could be auto-extracted, saving hours of manual work while maintaining full auditability.

## Solution

A single "Auto-Extract from OA Sources" button in the Search phase. After search results are loaded, the button triggers extraction from CT.gov and PubMed, shows a review panel where users verify every number against its source evidence, then commits selected values to the Extract table.

## Data Flow

```
Search Results (existing)
    | click "Auto-Extract"
    v
CT.gov API v2 --> fetch resultsSection for each NCT ID
PubMed API --> fetch structured abstracts for each PMID
    | parse
    v
Effect sizes: HR, OR, RR, MD with CIs and p-values
    | merge (CT.gov primary, PubMed fills gaps)
    v
Extraction Review Panel (user verifies every number)
    | user checks/unchecks, edits, accepts
    v
Extract table rows with source badges
    | user runs analysis (existing flow)
    v
Existing Analyze pipeline (unchanged)
```

## Extraction Engine

### CT.gov Results Parsing

Source: `resultsSection.outcomeMeasuresModule` from CT.gov API v2 study detail endpoint.

For each outcome measure:
- Extract `statisticalAnalyses` array -> paramType (Hazard Ratio, Odds Ratio, Risk Ratio), paramValue, ciLower, ciUpper, pValue
- Extract `measureValues` for continuous outcomes (mean, SD, count per arm)
- Extract enrollment per arm from `participantFlowModule`
- Map CT.gov outcome titles to user's PICO outcome field via fuzzy string matching (Levenshtein or token overlap)

### PubMed Abstract Parsing

Source: PubMed efetch API (XML), `AbstractText` elements with `NlmCategory="RESULTS"`.

Regex patterns for effect size extraction:
- HR: `HR\s*[=:]\s*(\d+\.?\d*)\s*[,;]?\s*(?:95%?\s*CI|CI)\s*[=:,]?\s*(\d+\.?\d*)\s*[-\u2013to]+\s*(\d+\.?\d*)`
- OR: `OR\s*[=:]\s*(\d+\.?\d*)` (same CI pattern)
- RR: `(?:RR|relative risk)\s*[=:]\s*(\d+\.?\d*)` (same CI pattern)
- MD: `(?:mean diff(?:erence)?|MD|difference)\s*[=:]\s*(-?\d+\.?\d*)` (same CI pattern)
- P-value: `[Pp]\s*[=<]\s*([\d.]+(?:\s*[x\u00d7]\s*10\s*[-\u2013]\s*\d+)?)`

Each extracted value retains the source sentence (verbatim text surrounding the match) for the evidence trail.

### Smart Merge

1. Match trials by NCT ID: CT.gov records have NCT IDs; PubMed records may contain NCT IDs in `DataBankList` or abstract text
2. When both sources have the same outcome for the same trial: CT.gov wins (structured, regulatory)
3. PubMed-only outcomes (not in CT.gov results): included, tagged `[PubMed-only]`
4. Unmatched PubMed records (no NCT ID linkage): included as standalone entries with PubMed source

## Effect Types

| Type | CT.gov Source | PubMed Regex | Scale |
|------|--------------|--------------|-------|
| HR | statisticalAnalyses paramType="Hazard Ratio" | `HR\s*[=:]` | Log (ratio) |
| OR | paramType="Odds Ratio" | `OR\s*[=:]` | Log (ratio) |
| RR | paramType="Risk Ratio" / "Relative Risk" | `RR\s*[=:]` | Log (ratio) |
| MD | measureValues with dispersion | `mean diff\|MD\|difference` | Linear |

## UI Changes

### 1. Search Phase: Auto-Extract Button

After `searchAll()` completes successfully, a new button row appears:

```html
<div id="autoExtractRow" style="display:none">
  <button id="autoExtractBtn" onclick="runAutoExtract()">
    Auto-Extract from OA Sources
  </button>
  <span id="autoExtractStatus"></span>
</div>
```

Progress indicator: "Fetching CT.gov results: 3/12... Parsing PubMed abstracts: 7/15..."

### 2. Extraction Review Panel

Appears between search results and the "proceed to Screen" flow. Key elements:

- **Per-trial accordion**: NCT ID, trial name, author/year, source badge (CT.gov / PubMed / Both)
- **Per-outcome rows within each trial**: effect type, point estimate, CI, p-value
- **Evidence column**: verbatim source text with the extracted number highlighted (yellow background)
  - CT.gov: field path e.g. "resultsSection > outcomeMeasures[2] > statisticalAnalyses[0]"
  - PubMed: PMID + highlighted sentence from Results section
- **Per-trial checkbox**: include/exclude entire trial
- **Per-outcome checkbox**: include/exclude individual outcomes
- **Editable values**: user can click any number to correct it inline
- **Summary header**: "N trials searched, M with results, K effect sizes extracted"
- **Action buttons**: "Accept Selected -> Extract Table" and "Export Evidence CSV"

### 3. Extract Table: Source Column

New `source` column in the Extract table with badges:
- Green `CT.gov` badge: structured results data
- Blue `PubMed` badge: abstract-parsed data
- Amber `Both` badge: CT.gov primary, PubMed confirmed
- Grey `Manual` badge: user-entered (existing behavior, default)

Provenance metadata stored per-row in the study object:
```js
{
  ...existingFields,
  extractionSource: 'ctgov' | 'pubmed' | 'both' | 'manual',
  extractionEvidence: {
    ctgov: { fieldPath: '...', rawValue: '...' },
    pubmed: { pmid: '...', sentence: '...', matchSpan: [start, end] }
  }
}
```

## Edge Cases

- Trial with no CT.gov results AND no parseable abstract: skipped, counted in "N trials with no extractable data"
- Abstract with multiple outcomes: extract all, each as separate row
- Non-English abstracts: skip (filter on PubMed `Language` field)
- Retracted articles: flag with warning badge (check PubMed `PublicationStatus`)
- CT.gov results with multiple arms: extract pairwise comparisons vs control arm (arm with role="ACTIVE_COMPARATOR" or "PLACEBO_COMPARATOR")
- Negative MD values: preserve sign (do NOT treat leading minus as formula injection)
- European decimals in abstracts: handled by existing European decimal regex guards from lessons.md

## What's NOT Included (YAGNI)

- Full-text PDF extraction
- LLM-based extraction
- Automatic analysis triggering (user still clicks Analyze)
- New config library or standalone app
- SMD or RD effect types
- Extraction from OpenAlex (metadata only, no effect sizes)

## Testing Strategy

- Unit-test regex patterns against 20+ known abstract formats (Finerenone, SGLT2, GLP-1, colchicine trials)
- Validate CT.gov parsing against the Finerenone database (finerenone_meta_analyses_database.md has gold-standard values)
- Selenium test: search "finerenone" -> auto-extract -> verify review panel shows correct values -> accept -> verify Extract table populated
- Edge case tests: trial with no results, abstract with no numbers, retracted article

## Dependencies

- Existing: `searchAll()`, `searchPubMed()`, `searchCTGov()`, `searchOpenAlex()`
- Existing: `rateLimitedFetch()`, `addStudyRow()`, Extract table CRUD
- New: CT.gov study detail API (`/api/v2/studies/{nctId}` with `fields=resultsSection`)
- New: PubMed efetch XML parsing for structured abstracts
