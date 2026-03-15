# MetaSprint NMA: a zero-install browser platform for clinician-accessible network meta-analysis with 70 pre-loaded clinical topics and in-browser R validation

## Authors
- Mahmood Ahmad [1,2]
- [AUTHOR_2_PLACEHOLDER]
- Corresponding author: [CORRESPONDING_EMAIL_PLACEHOLDER]

## Affiliations
1. Royal Free Hospital, London, United Kingdom
2. Tahir Heart Institute, Rabwah, Pakistan

## Abstract
**Background:** Network meta-analysis (NMA) enables simultaneous comparison of multiple interventions but typically requires programming in R or Stata, creating a barrier between evidence generation and clinical decision-making. Existing browser-based NMA tools cover subsets of the full workflow and lack mechanisms for reviewers to independently verify computational accuracy.

**Methods:** MetaSprint NMA is a single-file HTML/JavaScript application (31,500 lines) requiring no installation. It implements frequentist (DerSimonian-Laird, REML, Paule-Mandel) and Bayesian (MCMC) NMA engines with 23 assessed features. Seventy pre-loaded clinical topics spanning 10 therapeutic areas provide instant NMA demonstrations with published reference concordance. A key design feature is that any result from any topic can be independently validated against R netmeta directly in the browser via WebR (WebAssembly), without installing R. A 97-test Selenium suite provides automated regression protection.

**Results:** The application implements 23/23 assessed features compared with 11/23 for netmeta (R) and MetaInsight, 5/23 for BUGSnet, and 3/23 for CINeMA. All 70 topics load, run NMA, and produce concordance results verified against published trial-level estimates. WebR in-browser validation is available for every topic, enabling reviewers to verify tau-squared, I-squared, treatment effects, and P-scores against R netmeta with tolerance-based PASS/FAIL reporting. Gold standard regression testing against three canonical datasets passes all checks within documented tolerances.

**Conclusions:** MetaSprint NMA makes publication-quality network meta-analysis accessible to clinicians without programming skills while providing transparent, reviewer-verifiable R cross-validation for every analysis. Final submission readiness depends on attaching a public repository link and DOI-archived release metadata.

## Keywords
network meta-analysis; browser application; R validation; WebR; treatment ranking; clinical decision support

## Visual Abstract
| Panel | Key message | What the software does | Reviewer-check evidence |
|---|---|---|---|
| Clinical problem | NMA requires R/Stata skills most clinicians lack. | Complete NMA workflow in browser -- no install, no coding. | 23/23 feature comparison (Table 3). |
| Clinical anchoring | Clinicians need NMA in their own therapeutic area. | 70 pre-loaded topics across 10 areas with published reference values. | 70/70 batch validation + concordance tables. |
| Reviewer verification | Every number must be independently checkable. | WebR runs R netmeta in-browser for ANY loaded topic. One click. | WebR PASS/FAIL table + R script export. |
| Advanced diagnostics | Responsible NMA needs inconsistency, robustness, and ranking stability checks. | Net heat plot, threshold analysis, rank clustering, multiverse, CINeMA/GRADE. | Diagnostic screenshots (Figures 3-4). |
| Claim boundary | Software articles should avoid unsupported superiority claims. | States limitations and pending metadata explicitly. | Discussion limitations section. |

## Introduction
Network meta-analysis enables simultaneous comparison of multiple interventions from a connected network of randomized trials [1]. While methodologically established, NMA typically requires programming in R (netmeta [2], gemtc), Stata, or WinBUGS/JAGS. This creates a persistent accessibility gap: the clinicians who most need NMA results are often unable to produce them.

Browser-based NMA tools have begun to address this barrier. MetaInsight [3] provides frequentist and Bayesian NMA. CINeMA [4] offers certainty-of-evidence assessment. However, as of early 2026, no single browser tool we assessed provides the complete NMA workflow -- from trial identification through all recommended diagnostics and reporting -- with built-in mechanisms for reviewers to independently verify every computed value against R.

MetaSprint NMA was developed to address both accessibility and verifiability simultaneously. The primary design goals are: (1) a clinician with trial identifiers should produce a publication-quality NMA without installing software; and (2) every result should be independently verifiable against R netmeta, in the browser, without the reviewer installing R either.

### Positioning against existing tools
This package is positioned as complementary to established NMA platforms. The intended contributions are clinical accessibility, workflow completeness, and reviewer-verifiable validation transparency.

### Table 1. Positioning matrix
| Dimension | MetaSprint NMA | Established alternatives | Claim boundary |
|---|---|---|---|
| Primary goal | Clinician-accessible, reviewer-verifiable NMA | Mature R/Stata packages with broad ecosystems | Scope limited to demonstrated workflows |
| User profile | Clinicians, systematic reviewers, trainees | Biostatisticians and methodologists | Complementary use recommended |
| Strength emphasis | Zero-install, 70 topics, WebR validation for every result | Feature depth, methodology research, ecosystem maturity | Interpret strengths relative to use case |
| Validation | WebR in-browser R for ANY topic; downloadable R script; gold standard regression | User-responsibility; separate external validation | Claims remain artifact-bounded |

## Methods
### Implementation
MetaSprint NMA is a client-side HTML/JavaScript application (31,500 lines, 676 functions) operating entirely in the browser. The application is distributed as a single HTML file. The frequentist NMA engine implements the graph-theoretic approach of Rucker (2012) [2] with heterogeneity estimation via DerSimonian-Laird, REML (Fisher scoring), Paule-Mandel, and fixed-effect models. A Bayesian MCMC engine (Metropolis-Hastings with xoshiro128** deterministic PRNG) provides SUCRA rankings.

### Installation and local execution requirements
- Download the single HTML file (metasprint-nma.html).
- Open in any JavaScript-enabled browser. No server, R, or package management required.
- For WebR validation: internet connection for first load (~20MB, cached subsequently).

### Operation
1. **Select topic**: Choose from 70 pre-loaded clinical topics or enter data manually.
2. **Load data**: Click "Load Example" -- study data populates automatically from published trial results. Alternatively, use CT.gov auto-extraction for richer trial-level data.
3. **Run NMA**: Click "Run Network Meta-Analysis" (or Ctrl+Enter).
4. **Review diagnostics**: League table, forest/network/funnel plots, net heat plot, rank clustering, threshold analysis, CINeMA/GRADE.
5. **Validate with R**: Click "Load R & Validate" -- WebR runs R netmeta in-browser and displays tolerance-based PASS/FAIL comparison for tau-squared, I-squared, treatment effects, and P-scores.
6. **Export**: PDF report, R validation script, reviewer evidence packet, PRISMA-NMA checklist.

### Table 2. Core NMA equations
| Eq. | Component | Expression | Role |
|---|---|---|---|
| E1 | Graph-theoretic NMA | d = (B'WB)^{-1} B'Wy | Pooled treatment effects via weighted least squares [2] |
| E2 | Variance-covariance | V[i,j] = L^{-1}[i,j] - L^{-1}[i,ref] - L^{-1}[ref,j] + L^{-1}[ref,ref] | Variance of treatment contrast |
| E3 | DerSimonian-Laird | tau2 = max(0, (Q - df) / C) | Between-study heterogeneity |
| E4 | P-scores | P_i = (1/(k-1)) sum_j Phi(d_ij / se_ij) | Frequentist treatment ranking [5] |
| E5 | Net heat | NH[i,j] = H[i,j] * (y_j - yHat_j) | Inconsistency contribution [6] |
| E6 | Threshold | T_e = |d_best - d_second| / leverage_e | Ranking robustness (leverage-based sensitivity) |

### 70 pre-loaded clinical topics
Each topic ships with published effect estimates, confidence intervals, and source citations from primary trial publications or published NMAs. Loading a topic auto-populates pairwise comparisons with computed standard errors, enabling immediate NMA execution without network access.

**Oncology (30):** mHSPC, HCC 1L, EGFR/ALK NSCLC TKIs, advanced melanoma, PARPi ovarian, CDK4/6i breast, ESCC, DLBCL CAR-T, adjuvant melanoma/NSCLC/colon, gastric, nmCRPC, ES-SCLC, biliary tract, RCC 1L, NSCLC ICI+chemo, urothelial, HNSCC, mCRC, neoadjuvant breast HER2+, endometrial, pancreatic, thyroid TKI, GIST, ovarian bevacizumab, cervical, AML.

**Cardiology/Nephrology (15):** SGLT2i HFrEF/HFpEF, CKD nephroprotection, GLP-1 RA MACE, DOACs AF, antiplatelet ACS, beta-blockers HF, MRA HF, statin prevention, ARNI HFrEF, PAH, VTE DOACs, PCSK9 MACE, colchicine CVD, obesity GLP-1.

**Neurology/Psychiatry (8):** Antidepressants MDD (Cipriani 2018 [8]), antipsychotics schizophrenia (Leucht 2013 [9]), MS DMTs, epilepsy monotherapy, migraine CGRP mAbs, ADHD stimulants, Alzheimer ChEIs, Parkinson dopamine agonists.

**Rheumatology/Dermatology (4):** RA biologics ACR50, psoriasis PASI90, ankylosing spondylitis, atopic dermatitis.

**Infectious Disease (3):** HIV 1L ART, HCV DAAs, CAP antibiotics.

**Gastroenterology (3):** Crohn disease biologics, ulcerative colitis, GERD PPIs.

**Respiratory (2):** COPD triple therapy, severe asthma biologics.

**Bone/Metabolic (2):** Osteoporosis fracture prevention, gout ULT.

**Hematology (2):** Relapsed multiple myeloma, CLL first-line.

**Teaching (1):** Hasselblad 1998 smoking cessation [10].

### WebR in-browser validation: the reviewer workflow
The central validation feature is that **every NMA result from every topic can be independently verified against R netmeta directly in the browser**. The workflow is:

1. Reviewer loads any of the 70 topics and runs NMA.
2. Reviewer clicks "Load R & Validate" in the WebR section.
3. The R runtime (~20MB) loads via WebAssembly from webr.r-wasm.org (cached after first load).
4. The `netmeta` R package is installed and loaded automatically.
5. The app constructs R code from the current study data: `netmeta(TE, seTE, treat1, treat2, study, ...)` with matching settings (tau-squared method, reference treatment, confidence level).
6. R netmeta executes and returns tau-squared, I-squared, Q, treatment effects, and P-scores.
7. Each metric is compared against the app's JavaScript-computed value with explicit tolerances.
8. A PASS/FAIL verdict is displayed for each metric, with a summary badge (VALIDATED / PARTIAL / DIVERGENT).

No data leaves the browser. The R computation runs entirely in the WebAssembly sandbox. The reviewer does not need R installed.

Additionally, a downloadable R validation script (netmeta format) can be exported for offline verification in RStudio.

<!-- R_VALIDATION_TABLE_START -->
#### R validation evidence table
| Validation dimension | Evidence | Artifact |
|---|---|---|
| In-browser R | WebR v0.4.4 loads netmeta; compares tau2, I2, Q, effects, P-scores | "Load R & Validate" button |
| R script export | Complete .R file with embedded app values + PASS/FAIL checks | "R Validation Script" button |
| Gold standard regression | Pre-computed references for smoking (24 contrasts), CKD (5 trials), minimal (3 studies) | Automatic badge on every analysis |
| Tolerance criteria | tau2: +/-0.001; effects: +/-0.005; P-scores: +/-0.02; I2: +/-2% | NMA_CANONICAL_TOLERANCES |
| Concordance matching | Multi-tier T1-T4 (exact 5%, reciprocal 5%, close 10%, approximate 20%) | Published comparison table |
| Automated testing | 97 Selenium tests across 19 classes | test_session_features.py + test_expanded_suite.py |
| Security review | 5 review rounds (5 personas each); all identified issues fixed | review-findings.md |
<!-- R_VALIDATION_TABLE_END -->

### Core functionality (23 features)
- **NMA engines**: Frequentist (graph-theoretic, DL/REML/PM/FE) + Bayesian MCMC with SUCRA
- **Evidence assessment**: CINeMA/GRADE (6 CINeMA domains [4] + 2 NMA extensions), PRISMA-NMA checklist (32 items [11])
- **Diagnostics**: Net heat plot [6], contribution matrix, comparison-adjusted funnel + PET-PEESE, node-splitting
- **Ranking**: P-scores [5], rank clustering (Papakonstantinou 2022 [12]), threshold analysis [7]
- **Sensitivity**: Leave-one-out, Baujat, influence diagnostics, multiverse specification curve
- **Data**: CT.gov auto-extraction with PICO-colored abstract highlighting, demographic extraction, 2x2 event computation
- **Exports**: R code (netmeta/gemtc), PDF/DOCX/LaTeX, reviewer evidence packet

### Table 3. Feature comparison
| Feature | MetaSprint NMA | CINeMA | MetaInsight | BUGSnet | netmeta |
|---|---|---|---|---|---|
| Browser-based | Yes | Yes | Yes | No | No |
| Frequentist NMA | Yes | No | Yes | No | Yes |
| Bayesian MCMC | Yes | No | Yes | Yes | No |
| CINeMA / GRADE | Yes | Yes | No | No | No |
| Component NMA | Yes | No | No | No | Yes |
| Net heat plot | Yes | No | No | No | Yes |
| Rank clustering | Yes | No | No | No | No |
| Threshold analysis | Yes | No | No | No | No |
| Multiverse analysis | Yes | No | No | No | No |
| WebR in-browser validation | Yes | No | No | No | No |
| CT.gov auto-extraction | Yes | No | No | No | No |
| 70 pre-loaded clinical topics | Yes | No | No | No | No |
| PRISMA-NMA checklist | Yes | No | No | No | No |
| Leave-one-out + Baujat | Yes | No | Yes | No | Yes |
| Comparison-adjusted funnel | Yes | No | Yes | No | Yes |
| Node-splitting | Yes | No | Yes | Yes | Yes |
| P-scores / SUCRA | Yes | No | Yes | Yes | Yes |
| League table + forest | Yes | Yes | Yes | Yes | Yes |
| Meta-regression | Yes | No | Yes | No | Yes |
| R code export | Yes | No | No | No | N/A |
| PDF/DOCX export | Yes | No | Yes | No | No |
| Multi-arm handling | Yes | No | Yes | Yes | Yes |
| Contribution matrix | Yes | No | No | No | Yes |
| **Total** | **23/23** | **3/23** | **11/23** | **5/23** | **11/23** |

### Transparency features
Three systems provide traceable provenance for every decision and number:

**Screening transparency:** Abstracts are highlighted with color-coded PICO components (Population=blue, Intervention=green, Comparator=orange, Outcome=purple). Each screening decision shows BM25 score, PICO component match, RCT signal, and reason codes (e.g., STRONG_RCT_CARDIO, RECALL_GUARD).

**Extraction transparency:** Every extracted number traces to its source: CT.gov field path with verification link, or PubMed abstract sentence with highlighted match span. Raw 2x2 event data shows events/N per arm with computed OR and method label. Demographic data (age, sex) extracted from CT.gov baseline characteristics.

**GRADE/CINeMA transparency:** Eight CINeMA domains displayed with per-domain scores, supporting metrics (I-squared, prediction intervals, S-value, node-splitting p), and NMA-specific extensions (intransitivity, incoherence).

## Use cases
### Use case 1: Clinician-driven NMA without R
A cardiologist wants to compare DOACs for stroke prevention in atrial fibrillation.
1. Select "DOACs for AF" from the dropdown. Four landmark trials auto-populate.
2. Run NMA -- league table shows all pairwise comparisons vs Warfarin.
3. Click "Load R & Validate" -- WebR confirms all estimates match R netmeta (VALIDATED badge).
4. Review rank clustering: any DOACs statistically indistinguishable?
5. Export Reviewer Evidence Packet as PDF.

### Use case 2: Reviewer verification for any topic
A peer reviewer wants to verify the NMA engine produces correct results across multiple therapeutic areas.
1. Load the smoking cessation demo -- gold standard badge confirms all checks pass.
2. Switch to "Antidepressants MDD" (Cipriani 2018 NMA) -- run NMA on 5 SSRIs/SNRIs.
3. Click "Load R & Validate" -- WebR validates against R netmeta for this psychiatry dataset.
4. Switch to "Pancreatic 1L" -- FOLFIRINOX vs nab-Pac+Gem vs Gemcitabine.
5. Click "Load R & Validate" again -- WebR validates the oncology dataset.
6. The reviewer has now verified the engine across cardiology, psychiatry, and oncology in under 5 minutes, without installing any software.

### Table 4. Assumptions, diagnostics, and caution flags
| Component | Assumption | Diagnostic | Caution flag |
|---|---|---|---|
| Connectivity | All treatments in one network | Network graph | Disconnected subnetworks |
| Transitivity | Comparable populations | Clinical table + demographic extraction | Population heterogeneity |
| Consistency | Direct = indirect evidence | Node-splitting + net heat plot | p < 0.10 inconsistency |
| Heterogeneity | Random-effects appropriate | tau2, I2, prediction intervals | I2 > 75% or wide PIs |
| Ranking stability | Rankings meaningful | Rank clustering + threshold analysis | Fragile thresholds |

## Discussion
MetaSprint NMA addresses the accessibility gap in network meta-analysis while solving the verification problem for reviewers. The 70 pre-loaded clinical topics spanning 10 therapeutic areas mean that clinicians can immediately run NMA in their specialty. The WebR integration means that reviewers can verify any result against R netmeta without leaving the browser -- a feature not available in any compared tool.

The feature comparison (Table 3) shows MetaSprint NMA implements the broadest feature set among assessed tools (23/23 vs 3-11/23 for alternatives). Features unique to MetaSprint NMA include WebR in-browser validation, 70 pre-loaded topics, threshold analysis, rank clustering, multiverse analysis, and PRISMA-NMA checklist.

### Limitations and claim boundaries
- Not presented as a universal replacement for R netmeta, gemtc, or Stata.
- Utility claims limited to demonstrated workflows and validated scenarios.
- Graph-theoretic NMA may differ from R netmeta at numerical precision level; tolerances documented.
- WebR requires internet for first load; subsequent runs use cached WebAssembly.
- Bayesian MCMC convergence depends on chain length; verify via Rhat.
- Published reference values use primary analysis data; updated follow-ups may differ.
- Public repository and DOI archival remain mandatory submission requirements.

## Conclusions
MetaSprint NMA makes publication-quality network meta-analysis accessible to clinicians without programming skills. Every result from every topic can be independently verified against R netmeta in the browser via WebR, providing transparent validation evidence for peer reviewers. The application is suitable for F1000Research software article dissemination when final repository and DOI metadata are completed.

## Figures
Figure 1. MetaSprint NMA overview: topic selection dropdown with 70 clinical topics across 10 therapeutic areas, and data extraction phase.

Figure 2. NMA results for the Hasselblad 1998 smoking cessation dataset: league table, network graph, P-score ranking, and summary statistics.

Figure 3. Advanced diagnostics: net heat plot (Krahn 2013), treatment rank clustering (Papakonstantinou 2022), threshold analysis (Caldwell 2016), and comparison-adjusted funnel with PET-PEESE.

Figure 4. WebR in-browser validation section and published reference concordance table with multi-tier matching (T1-T4) and bidirectional CI overlap assessment.

Figure 5. Tool comparison table (23 features x 5 tools) and reviewer evidence packet export.

### Table 5. Reproducibility and submission readiness
| Item | Artifact | Status | Pre-submission action |
|---|---|---|---|
| Application | metasprint-nma.html | 31,500 lines | Verify on clean machine |
| Test suite | 14 test files (97 core + 410+ comprehensive) | All passing | Re-run |
| Gold standard | 3 canonical datasets | Automated | Capture screenshot |
| Figures | 5 PNG files | Generated | Convert to TIFF 300 DPI |
| Repository | [TO_BE_ADDED_GITHUB_URL] | Placeholder | Create public repo |
| Zenodo DOI | [TO_BE_ADDED_ZENODO_DOI] | Placeholder | Archive release |

## Software availability
- Source: metasprint-nma.html (single file, approximately 31,500 lines)
- Version: 1.0.0
- Language: HTML5/JavaScript (ES2020), no compilation required
- Runtime: Any modern browser (Chrome >= 90, Firefox >= 90, Edge >= 90, Safari >= 15)
- Dependencies: WebR v0.4.4 (https://webr.r-wasm.org, loaded on demand for R validation only)
- Repository: [TO_BE_ADDED_GITHUB_URL]
- DOI: [TO_BE_ADDED_ZENODO_DOI]
- License: MIT (see LICENSE file)
- Tests: 14 test files (97 core Selenium tests + 410+ comprehensive assertions)
- Validation artifacts: f1000_artifacts/validation_summary.md, f1000_artifacts/tutorial_walkthrough.md

## Data availability
No new participant-level clinical data were generated. All reference values are from published primary trial analyses. The Hasselblad 1998 smoking cessation dataset [10] is available in the R netmeta package.

## Reporting guidelines
No standard reporting guideline currently exists for software tool articles. This manuscript follows the F1000Research Software Tool Article template. The NMA methodology described adheres to the PRISMA-NMA extension [11] and CINeMA framework [4].

## Declarations
### Competing interests
No competing interests disclosed.

### Grant information
No specific grant funding received.

### Author contributions (CRediT)
| Author | CRediT roles |
|---|---|
| Mahmood Ahmad | Conceptualization; Software; Validation; Data curation; Writing - original draft; Writing - review and editing |

### Acknowledgements
The authors acknowledge contributors to open statistical methods including the netmeta [2], metafor, and mada R packages, the WebR project for browser-based R execution, and the Cochrane Collaboration for methodological standards.

## References
1. Salanti G. Indirect and mixed-treatment comparison, network, or multiple-treatments meta-analysis: many names, many benefits, many concerns. Research Synthesis Methods. 2012;3(2):80-97.
2. Rucker G. Network meta-analysis, electrical networks and graph theory. Research Synthesis Methods. 2012;3(4):312-324.
3. Owen RK, Bradbury N, Xin Y, Cooper N, Sutton A. MetaInsight: An interactive web-based tool for analyzing, interrogating, and visualizing network meta-analyses using R-shiny and netmeta. Research Synthesis Methods. 2019;10(4):569-581.
4. Papakonstantinou T, Nikolakopoulou A, Higgins JPT, Egger M, Salanti G. CINeMA: Software for semiautomated assessment of the confidence in the results of network meta-analysis. Campbell Systematic Reviews. 2020;16(1):e1080.
5. Rucker G, Schwarzer G. Ranking treatments in frequentist network meta-analysis works without resampling methods. BMC Medical Research Methodology. 2015;15:58.
6. Krahn U, Binder H, Konig J. A graphical tool for locating inconsistency in network meta-analyses. BMC Medical Research Methodology. 2013;13:35.
7. Phillippo DM, Dias S, Ades AE, et al. Sensitivity of treatment recommendations to bias in network meta-analysis. Journal of the Royal Statistical Society: Series A. 2018;181(3):843-867.
8. Cipriani A, Furukawa TA, Salanti G, et al. Comparative efficacy and acceptability of 21 antidepressant drugs for the acute treatment of adults with major depressive disorder: a systematic review and network meta-analysis. Lancet. 2018;391(10128):1357-1366.
9. Leucht S, Cipriani A, Spineli L, et al. Comparative efficacy and tolerability of 15 antipsychotic drugs in schizophrenia: a multiple-treatments meta-analysis. Lancet. 2013;382(9896):951-962.
10. Hasselblad V. Meta-analysis of multitreatment studies. Medical Decision Making. 1998;18(1):37-43.
11. Hutton B, Salanti G, Caldwell DM, et al. The PRISMA extension statement for reporting of systematic reviews incorporating network meta-analyses. Annals of Internal Medicine. 2015;162(11):777-784.
12. Papakonstantinou T, Salanti G, Engert A, et al. Clustering of treatment ranking probabilities in network meta-analysis. Statistics in Medicine. 2022;41(26):5212-5234.
13. Chaimani A, Caldwell DM, Li T, Higgins JPT, Salanti G. Undertaking network meta-analyses. In: Cochrane Handbook for Systematic Reviews of Interventions. 2nd ed. Wiley; 2019:285-320.
