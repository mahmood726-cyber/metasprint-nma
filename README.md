# MetaSprint NMA

**Zero-install browser-based network meta-analysis platform with 70 pre-loaded clinical topics and integrated R cross-validation.**

## Quick Start

1. Open `metasprint-nma.html` in any modern browser (Chrome, Firefox, Edge, Safari)
2. Select a clinical topic from the dropdown (70 topics across 10 therapeutic areas)
3. Click **Load Example** -- study data populates automatically from published trial results
4. Click **Run Network Meta-Analysis** (or press `Ctrl+Enter`)
5. Review results: league table, forest plot, network graph, P-scores, diagnostics
6. Click **Load R & Validate** to verify results against R netmeta in your browser via WebR

No installation, no server, no R required. All computation runs locally in the browser.

## Features (23/23 assessed)

| Category | Features |
|---|---|
| **NMA Engines** | Frequentist (DL, REML, PM, FE) + Bayesian MCMC with SUCRA |
| **Evidence Assessment** | CINeMA/GRADE (8 domains), PRISMA-NMA checklist (32 items) |
| **Diagnostics** | Net heat plot, comparison-adjusted funnel + PET-PEESE, node-splitting, contribution matrix |
| **Ranking** | P-scores, rank clustering (silhouette-optimal k-means), threshold analysis |
| **Sensitivity** | Leave-one-out, Baujat, influence diagnostics, multiverse specification curve |
| **Data Sources** | CT.gov auto-extraction, PubMed abstract parsing, 2x2 event computation |
| **Validation** | WebR in-browser R, downloadable R script, gold standard regression (3 datasets) |
| **Reporting** | PDF/DOCX/LaTeX export, R code (netmeta/gemtc), reviewer evidence packet |

## 70 Clinical Topics

- **Oncology (30):** mHSPC, HCC, EGFR/ALK NSCLC, melanoma, PARPi ovarian, CDK4/6i breast, ESCC, DLBCL CAR-T, adjuvant melanoma/NSCLC/colon, gastric, nmCRPC, SCLC, BTC, urothelial, HNSCC, mCRC, endometrial, pancreatic, thyroid, GIST, ovarian, cervical, AML
- **Cardiology/Nephrology (15):** SGLT2i HF/HFpEF, CKD, GLP-1 MACE, DOACs AF, antiplatelet ACS, beta-blockers HF, MRA HF, statin, ARNI, PAH, VTE DOACs, PCSK9, colchicine, obesity GLP-1
- **Neurology/Psychiatry (8):** Antidepressants (Cipriani 2018), antipsychotics (Leucht 2013), MS DMTs, epilepsy, migraine CGRP, ADHD, Alzheimer ChEIs, Parkinson DA
- **Rheumatology/Dermatology (4):** RA biologics, psoriasis biologics, ankylosing spondylitis, atopic dermatitis
- **Infectious Disease (3):** HIV ART, HCV DAAs, CAP antibiotics
- **Gastroenterology (3):** Crohn biologics, UC biologics, GERD PPIs
- **Respiratory (2):** COPD triple therapy, severe asthma biologics
- **Bone/Metabolic (2):** Osteoporosis, gout ULT
- **Hematology (2):** Multiple myeloma, CLL
- **Teaching (1):** Hasselblad 1998 smoking cessation

## R Cross-Validation

Every NMA result can be independently verified against R netmeta through three mechanisms:

1. **WebR in-browser**: Click "Load R & Validate" -- R runs via WebAssembly directly in your browser
2. **Downloadable R script**: Click "R Validation Script" -- generates a complete .R file with tolerance-based PASS/FAIL checks
3. **Gold standard regression**: Runs automatically on every analysis against pre-computed reference values

## Testing

```bash
python test_session_features.py    # 49 tests
python test_expanded_suite.py      # 48 tests
python test_nma_comprehensive.py   # 410+ assertions
```

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Run NMA analysis |
| `Ctrl+S` | Save to localStorage |
| `Ctrl+Z` / `Ctrl+Y` | Undo / Redo |
| `?` | Toggle help panel |
| `I` / `E` / `M` | Include / Exclude / Maybe (screening phase) |

## Citation

If you use MetaSprint NMA in your research, please cite the F1000Research software article (in preparation).

## License

MIT License. See [LICENSE](LICENSE) file.
