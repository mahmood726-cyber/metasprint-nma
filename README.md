# MetaSprint NMA

Zero-install browser-based network meta-analysis platform with 70 pre-loaded clinical topics and integrated R cross-validation.

## Quick Start

1. Open `metasprint-nma.html` in Chrome, Firefox, Edge, or Safari.
2. Select a clinical topic from the dropdown.
3. Click **Load Example** to populate study data from published trial results.
4. Click **Run Network Meta-Analysis** or press `Ctrl+Enter`.
5. Review the league table, forest plot, network graph, ranking output, and diagnostics.
6. Click **Load R & Validate** to compare against `netmeta` in-browser via WebR.

No installation, server, or desktop R session is required for end users.

## Features

| Category | Features |
|---|---|
| NMA engines | Frequentist (DL, REML, PM, FE) and Bayesian MCMC with SUCRA |
| Evidence assessment | CINeMA/GRADE, PRISMA-NMA checklist |
| Diagnostics | Net heat plot, comparison-adjusted funnel, PET-PEESE, node-splitting, contribution matrix |
| Ranking | P-scores, rank clustering, threshold analysis |
| Sensitivity | Leave-one-out, Baujat, influence diagnostics, multiverse specification curve |
| Data sources | CT.gov auto-extraction, PubMed abstract parsing, 2x2 event computation |
| Validation | WebR parity, downloadable R script, gold-standard regression datasets |
| Reporting | PDF, DOCX, LaTeX, R code export, reviewer evidence packet |

## Clinical Topic Library

The app ships with 70 topics across oncology, cardiology, nephrology, neurology, psychiatry, rheumatology, dermatology, infectious disease, gastroenterology, respiratory medicine, bone/metabolic medicine, hematology, and teaching examples.

## R Cross-Validation

Every analysis can be checked through three paths:

1. WebR in-browser validation.
2. Downloadable `.R` validation script.
3. Gold-standard regression checks against reference datasets.

## Testing

```bash
python test_session_features.py
python test_expanded_suite.py
python test_nma_comprehensive.py
```

`requirements.txt` is only for local validation automation. End users only need a browser.

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Run NMA analysis |
| `Ctrl+S` | Save to localStorage |
| `Ctrl+Z` / `Ctrl+Y` | Undo / redo |
| `?` | Toggle help panel |
| `I` / `E` / `M` | Include / exclude / maybe in screening views |

## Citation

Use `CITATION.cff` for software citation metadata. Update this section once the F1000Research software article and DOI are available.

## License

MIT. See `LICENSE`.
