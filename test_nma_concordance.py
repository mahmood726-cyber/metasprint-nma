"""
NMA Concordance Validation: Engine vs Published NMA Results
============================================================
Compares our automated CT.gov extraction + NMA engine against
published NMA pooled estimates from peer-reviewed meta-analyses.

Metrics:
  - Per-trial HR concordance (extracted vs published)
  - Log-HR mean absolute error (MAE)
  - Rank concordance (Spearman rho of P-scores vs published ranking)
  - Indirect estimate concordance (NMA league table vs published)

Reference NMAs (14 topics):
  1. CKD Nephroprotection: CREDENCE, DAPA-CKD, EMPA-KIDNEY, FIDELIO-DKD
  2. 1L HCC OS: Fulgenzi 2022 (PMID 35970037) + trial publications
  3. GLP-1 RA CVOT MACE: Sattar 2021 (PMID 34425083) + trial publications
  4. Adj RCC DFS: KEYNOTE-564, IMmotion010, CheckMate-914 publications
  5. SGLT2i HF: DAPA-HF, EMPEROR-Reduced, EMPEROR-Preserved
  6. CDK4/6i Breast PFS: PALOMA-2, MONALEESA-2, MONARCH-3
  7. PARPi Ovarian PFS: SOLO2, NOVA, ARIEL3
  8. Adj Melanoma RFS: KEYNOTE-054, COMBI-AD, KEYNOTE-716
  9. 2L DLBCL CAR-T EFS: ZUMA-7, TRANSFORM, BELINDA
  10. 1L ESCC ICI+Chemo OS: KEYNOTE-590, CheckMate-648, RATIONALE-306
  11. Adj NSCLC DFS: IMpower010, PEARLS/KN-091, ADAURA
  12. nmCRPC MFS: SPARTAN, PROSPER, ARAMIS
  13. 1L ES-SCLC OS: IMpower133, CASPIAN
  14. 1L Biliary Tract OS: TOPAZ-1, KEYNOTE-966
"""
import io, sys, os, time, json, math, traceback
if 'pytest' not in sys.modules and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metasprint-nma.html')
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')

# ===================================================================
# TOPIC CONFIGURATIONS with PUBLISHED REFERENCE VALUES
# ===================================================================

TOPICS = [
    # -- Topic 1: CKD Nephroprotection — Kidney Composite (HR) --
    # Published: CREDENCE (Perkovic NEJM 2019), DAPA-CKD (Heerspink NEJM 2020),
    #            EMPA-KIDNEY (Herrington NEJM 2023), FIDELIO-DKD (Bakris NEJM 2020)
    # Non-oncology star network: 4 drugs vs Placebo. Primary endpoint = kidney composite.
    # CT.gov posts primary completion data → matches published HRs closely.
    {
        'name': 'CKD Nephroprotection (kidney composite)',
        'reference_nma': 'Individual trial publications: CREDENCE, DAPA-CKD, EMPA-KIDNEY, FIDELIO-DKD',
        'pico': {
            'P': 'Adults with chronic kidney disease (diabetic and non-diabetic)',
            'I': 'SGLT2 inhibitors or finerenone',
            'C': 'Placebo',
            'O': 'Kidney disease progression composite',
        },
        'trials': [
            {'nctId': 'NCT02065791', 'pmid': '30990260', 'title': 'CREDENCE (Canagliflozin CKD)',
             'authors': 'Perkovic V', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT03036150', 'pmid': '32970396', 'title': 'DAPA-CKD (Dapagliflozin CKD)',
             'authors': 'Heerspink HJL', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT03594110', 'pmid': '36331190', 'title': 'EMPA-KIDNEY (Empagliflozin CKD)',
             'authors': 'Herrington WG', 'year': '2023', 'source': 'ctgov'},
            {'nctId': 'NCT02540993', 'pmid': '33264825', 'title': 'FIDELIO-DKD (Finerenone DKD)',
             'authors': 'Bakris GL', 'year': '2020', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'kidney',
        'alt_keywords': ['renal', 'composite', 'creatinine', 'egfr', 'eskd'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'canagliflozin': 'Canagliflozin',
            'dapagliflozin': 'Dapagliflozin',
            'empagliflozin': 'Empagliflozin',
            'finerenone': 'Finerenone',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Canagliflozin': {'hr': 0.70, 'lo': 0.59, 'hi': 0.82, 'source': 'CREDENCE kidney composite, Perkovic NEJM 2019'},
            'Dapagliflozin': {'hr': 0.61, 'lo': 0.51, 'hi': 0.72, 'source': 'DAPA-CKD kidney composite, Heerspink NEJM 2020'},
            'Empagliflozin': {'hr': 0.72, 'lo': 0.64, 'hi': 0.82, 'source': 'EMPA-KIDNEY kidney progression, Herrington NEJM 2023'},
            'Finerenone': {'hr': 0.82, 'lo': 0.73, 'hi': 0.93, 'source': 'FIDELIO-DKD kidney composite, Bakris NEJM 2020'},
        },
        'published_ranking': ['Dapagliflozin', 'Canagliflozin', 'Empagliflozin', 'Finerenone', 'Placebo'],
    },

    # -- Topic 2: 1L HCC OS vs Sorafenib --
    # Reference NMA: Fulgenzi 2022 (PMID 35970037), Fong 2023 (PMID 36872922)
    {
        'name': '1L HCC ICI OS (Fulgenzi concordance)',
        'reference_nma': 'Fulgenzi CAM et al. Eur J Cancer 2022; PMID 35970037',
        'pico': {
            'P': 'Unresectable hepatocellular carcinoma, first-line',
            'I': 'Immune checkpoint inhibitor combination or monotherapy',
            'C': 'Sorafenib',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT03434379', 'pmid': '32402160', 'title': 'IMbrave150 (Atezo+Bev vs Sorafenib)',
             'authors': 'Finn RS', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT03298451', 'pmid': '38319892', 'title': 'HIMALAYA (Durva+Treme vs Sorafenib)',
             'authors': 'Abou-Alfa GK', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT02576509', 'pmid': '34914889', 'title': 'CheckMate 459 (Nivo vs Sorafenib)',
             'authors': 'Yau T', 'year': '2022', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'alt_keywords': ['survival', 'death', 'os'],
        'effect_type': 'HR',
        'common_comparator': 'Sorafenib',
        'norm_map': {
            'atezolizumab': 'Atezo+Bev',
            'bevacizumab': 'Atezo+Bev',
            'durvalumab': 'Durva+Treme',
            'tremelimumab': 'Durva+Treme',
            'treme': 'Durva+Treme',
            'nivolumab': 'Nivolumab',
            'sorafenib': 'Sorafenib',
            'sora': 'Sorafenib',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Atezo+Bev': {'hr': 0.58, 'lo': 0.42, 'hi': 0.79, 'source': 'IMbrave150 primary, Finn 2020 NEJM'},
            'Durva+Treme': {'hr': 0.78, 'lo': 0.65, 'hi': 0.93, 'source': 'HIMALAYA STRIDE primary, Abou-Alfa NEJM Evid 2022 (96.02% CI)'},
            'Nivolumab': {'hr': 0.85, 'lo': 0.72, 'hi': 1.02, 'source': 'CheckMate-459, Yau 2022'},
        },
        'published_ranking': ['Atezo+Bev', 'Durva+Treme', 'Nivolumab', 'Sorafenib'],
    },

    # -- Topic 3: GLP-1 RA CVOT MACE --
    # Reference NMA: Sattar 2021 (PMID 34425083), Kristensen 2019 (PMID 30739519)
    {
        'name': 'GLP-1 RA CVOT MACE (Sattar concordance)',
        'reference_nma': 'Sattar N et al. Lancet Diabetes Endocrinol 2021; PMID 34425083',
        'pico': {
            'P': 'Adults with type 2 diabetes at high cardiovascular risk',
            'I': 'GLP-1 receptor agonist',
            'C': 'Placebo',
            'O': 'Major adverse cardiovascular events (MACE)',
        },
        'trials': [
            {'nctId': 'NCT01179048', 'pmid': '27295427', 'title': 'LEADER (Liraglutide CVOT)',
             'authors': 'Marso SP', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT01720446', 'pmid': '27633186', 'title': 'SUSTAIN-6 (Semaglutide CVOT)',
             'authors': 'Marso SP', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT02465515', 'pmid': '30291013', 'title': 'Harmony Outcomes (Albiglutide CVOT)',
             'authors': 'Hernandez AF', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT01394952', 'pmid': '31189511', 'title': 'REWIND (Dulaglutide CVOT)',
             'authors': 'Gerstein HC', 'year': '2019', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'mace',
        'alt_keywords': ['cardiovascular', 'composite', 'cv death', 'myocardial', 'stroke', 'major adverse'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'liraglutide': 'Liraglutide',
            'semaglutide': 'Semaglutide',
            'albiglutide': 'Albiglutide',
            'dulaglutide': 'Dulaglutide',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Liraglutide': {'hr': 0.87, 'lo': 0.78, 'hi': 0.97, 'source': 'LEADER, Marso NEJM 2016'},
            'Semaglutide': {'hr': 0.74, 'lo': 0.58, 'hi': 0.95, 'source': 'SUSTAIN-6, Marso NEJM 2016'},
            'Albiglutide': {'hr': 0.78, 'lo': 0.68, 'hi': 0.90, 'source': 'HARMONY, Hernandez Lancet 2018'},
            'Dulaglutide': {'hr': 0.88, 'lo': 0.79, 'hi': 0.99, 'source': 'REWIND, Gerstein Lancet 2019'},
        },
        'published_ranking': ['Semaglutide', 'Albiglutide', 'Liraglutide', 'Dulaglutide', 'Placebo'],
    },

    # -- Topic 4: Adjuvant RCC DFS --
    # From Round 4 Topic 2 — validated already, now add published reference HRs
    {
        'name': 'Adjuvant RCC ICI DFS (trial concordance)',
        'reference_nma': 'Individual trial publications: KEYNOTE-564, IMmotion010, CheckMate-914',
        'pico': {
            'P': 'Adults with resected renal cell carcinoma at high risk of recurrence',
            'I': 'Immune checkpoint inhibitor adjuvant therapy',
            'C': 'Placebo',
            'O': 'Disease-free survival',
        },
        'trials': [
            {'nctId': 'NCT03142334', 'pmid': '34407342', 'title': 'KEYNOTE-564 (Pembrolizumab adj RCC)',
             'authors': 'Choueiri TK', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT03024996', 'pmid': '36099926', 'title': 'IMmotion010 (Atezolizumab adj RCC)',
             'authors': 'Pal SK', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT03138512', 'pmid': '36774933', 'title': 'CheckMate-914 (Nivo+Ipi adj RCC)',
             'authors': 'Motzer RJ', 'year': '2023', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'disease-free',
        'alt_keywords': ['dfs', 'disease free', 'recurrence', 'relapse-free'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'pembrolizumab': 'Pembrolizumab',
            'atezolizumab': 'Atezolizumab',
            'nivolumab': 'Nivo+Ipi',
            'ipilimumab': 'Nivo+Ipi',
            'nivo': 'Nivo+Ipi',
            'placebo': 'Placebo',
            'treatment part a:': 'Nivo+Ipi',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Pembrolizumab': {'hr': 0.68, 'lo': 0.53, 'hi': 0.87, 'source': 'KEYNOTE-564, Choueiri NEJM 2021'},
            'Atezolizumab': {'hr': 0.93, 'lo': 0.75, 'hi': 1.15, 'source': 'IMmotion010, Pal JCO 2022'},
            'Nivo+Ipi': {'hr': 0.92, 'lo': 0.71, 'hi': 1.19, 'source': 'CheckMate-914, Motzer NEJM 2023'},
        },
        'published_ranking': ['Pembrolizumab', 'Nivo+Ipi', 'Atezolizumab', 'Placebo'],
    },

    # -- Topic 5: SGLT2i Heart Failure Composite (CV death + HHF) --
    # Reference: Individual trials + Zannad 2020 meta-analysis (PMID 32865377)
    {
        'name': 'SGLT2i HF Composite (trial concordance)',
        'reference_nma': 'Individual trial publications: DAPA-HF, EMPEROR-Reduced, EMPEROR-Preserved',
        'pico': {
            'P': 'Adults with heart failure (HFrEF or HFpEF)',
            'I': 'SGLT2 inhibitor',
            'C': 'Placebo',
            'O': 'CV death or hospitalization for heart failure',
        },
        'trials': [
            {'nctId': 'NCT03036124', 'pmid': '31535829', 'title': 'DAPA-HF (Dapagliflozin HFrEF)',
             'authors': 'McMurray JJV', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT03057977', 'pmid': '32865377', 'title': 'EMPEROR-Reduced (Empagliflozin HFrEF)',
             'authors': 'Packer M', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT03057951', 'pmid': '34449189', 'title': 'EMPEROR-Preserved (Empagliflozin HFpEF)',
             'authors': 'Anker SD', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'cardiovascular',
        'alt_keywords': ['cv death', 'heart failure', 'hospitalization', 'composite', 'hf'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'dapagliflozin': 'Dapagliflozin',
            'dapa': 'Dapagliflozin',
            'empagliflozin': 'Empagliflozin',
            '10 mg empagliflozin': 'Empagliflozin',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Dapagliflozin': {'hr': 0.74, 'lo': 0.65, 'hi': 0.85, 'source': 'DAPA-HF, McMurray NEJM 2019'},
            # NMA pools EMPEROR-Reduced (HR 0.75) and EMPEROR-Preserved (HR 0.79) under 'Empagliflozin'
            # Pooled estimate expected ~0.77; using EMPEROR-Reduced as primary reference
            'Empagliflozin': {'hr': 0.75, 'lo': 0.65, 'hi': 0.86, 'source': 'EMPEROR-Reduced, Packer NEJM 2020'},
        },
        'published_ranking': ['Dapagliflozin', 'Empagliflozin', 'Placebo'],
    },

    # -- Topic 6: CDK4/6i 1L HR+ Breast Cancer PFS --
    # Published NMA: BMC Cancer 2025; Deng 2024 JCO
    # 3 CDK4/6 inhibitors + AI vs AI alone. Star network.
    {
        'name': 'CDK4/6i 1L HR+ Breast PFS',
        'reference_nma': 'Individual trial publications: PALOMA-2, MONALEESA-2, MONARCH-3',
        'pico': {
            'P': 'Postmenopausal HR+/HER2- advanced breast cancer, first-line',
            'I': 'CDK4/6 inhibitor + aromatase inhibitor',
            'C': 'Aromatase inhibitor alone',
            'O': 'Progression-free survival',
        },
        'trials': [
            {'nctId': 'NCT01740427', 'pmid': '27959613', 'title': 'PALOMA-2 (Palbociclib+Letrozole)',
             'authors': 'Finn RS', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT01958021', 'pmid': '27717303', 'title': 'MONALEESA-2 (Ribociclib+Letrozole)',
             'authors': 'Hortobagyi GN', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT02246621', 'pmid': '28968163', 'title': 'MONARCH-3 (Abemaciclib+NSAI)',
             'authors': 'Goetz MP', 'year': '2017', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'progression',
        'alt_keywords': ['pfs', 'progression-free', 'disease progression'],
        'effect_type': 'HR',
        'common_comparator': 'AI',
        'norm_map': {
            'palbociclib': 'Palbociclib+AI',
            'pd-0332991': 'Palbociclib+AI',
            'ribociclib': 'Ribociclib+AI',
            'lee011': 'Ribociclib+AI',
            'abemaciclib': 'Abemaciclib+AI',
            'ly2835219': 'Abemaciclib+AI',
            'letrozole': 'AI',
            'nsai': 'AI',
            'nonsteroidal aromatase': 'AI',
            'placebo': 'AI',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Palbociclib+AI': {'hr': 0.58, 'lo': 0.46, 'hi': 0.72, 'source': 'PALOMA-2, Finn NEJM 2016'},
            'Ribociclib+AI': {'hr': 0.56, 'lo': 0.43, 'hi': 0.72, 'source': 'MONALEESA-2, Hortobagyi NEJM 2016'},
            'Abemaciclib+AI': {'hr': 0.54, 'lo': 0.41, 'hi': 0.72, 'source': 'MONARCH-3, Goetz JCO 2017'},
        },
        'published_ranking': ['Abemaciclib+AI', 'Ribociclib+AI', 'Palbociclib+AI', 'AI'],
    },

    # -- Topic 7: PARPi Maintenance Ovarian PFS --
    # Published NMA: Oncotarget 2019; Gynecol Oncol 2021
    # 3 PARP inhibitors vs Placebo. Clean star network.
    {
        'name': 'PARPi Maintenance Ovarian PFS',
        'reference_nma': 'Individual trial publications: SOLO2, NOVA, ARIEL3',
        'pico': {
            'P': 'Platinum-sensitive recurrent ovarian cancer',
            'I': 'PARP inhibitor maintenance (olaparib, niraparib, rucaparib)',
            'C': 'Placebo',
            'O': 'Progression-free survival',
        },
        'trials': [
            {'nctId': 'NCT01874353', 'pmid': '28754483', 'title': 'SOLO2 (Olaparib maintenance)',
             'authors': 'Pujade-Lauraine E', 'year': '2017', 'source': 'ctgov'},
            {'nctId': 'NCT01847274', 'pmid': '27717299', 'title': 'NOVA (Niraparib maintenance)',
             'authors': 'Mirza MR', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT01968213', 'pmid': '28916367', 'title': 'ARIEL3 (Rucaparib maintenance)',
             'authors': 'Coleman RL', 'year': '2017', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'progression',
        'alt_keywords': ['pfs', 'progression-free', 'disease progression'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'olaparib': 'Olaparib',
            'niraparib': 'Niraparib',
            'rucaparib': 'Rucaparib',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Olaparib': {'hr': 0.30, 'lo': 0.22, 'hi': 0.41, 'source': 'SOLO2 all-comers, Pujade-Lauraine Lancet Oncol 2017'},
            # NOVA CT.gov reports gBRCA cohort (HR 0.27), not all-comers (HR 0.38)
            'Niraparib': {'hr': 0.27, 'lo': 0.17, 'hi': 0.41, 'source': 'NOVA gBRCA cohort, Mirza NEJM 2016'},
            'Rucaparib': {'hr': 0.36, 'lo': 0.30, 'hi': 0.45, 'source': 'ARIEL3 all-comers, Coleman Lancet 2017'},
        },
        # Ranking based on published_hrs values: Niraparib gBRCA 0.27 < Olaparib 0.30 < Rucaparib 0.36
        'published_ranking': ['Niraparib', 'Olaparib', 'Rucaparib', 'Placebo'],
    },

    # -- Topic 8: Adjuvant Melanoma RFS --
    # Published NMA: Lancet Oncol 2020
    # 2 treatments (pembrolizumab, dabrafenib+trametinib) vs Placebo
    {
        'name': 'Adjuvant Melanoma RFS',
        'reference_nma': 'Individual trial publications: KEYNOTE-054, COMBI-AD, KEYNOTE-716',
        'pico': {
            'P': 'Resected stage III or stage IIB/C melanoma',
            'I': 'Adjuvant immunotherapy or targeted therapy',
            'C': 'Placebo',
            'O': 'Relapse-free survival',
        },
        'trials': [
            {'nctId': 'NCT02362594', 'pmid': '29658430', 'title': 'KEYNOTE-054 (Pembro adj stage III)',
             'authors': 'Eggermont AMM', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT01682083', 'pmid': '28891408', 'title': 'COMBI-AD (Dab+Tram adj BRAF+)',
             'authors': 'Long GV', 'year': '2017', 'source': 'ctgov'},
            {'nctId': 'NCT03553836', 'pmid': '35367007', 'title': 'KEYNOTE-716 (Pembro adj stage IIB/C)',
             'authors': 'Luke JJ', 'year': '2022', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'relapse',
        'alt_keywords': ['recurrence', 'rfs', 'dfs', 'disease-free'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'pembrolizumab': 'Pembrolizumab',
            'mk-3475': 'Pembrolizumab',
            'keytruda': 'Pembrolizumab',
            'placebos': 'Placebo',  # COMBI-AD "Dabrafenib and trametinib placebos"
            'dabrafenib': 'Dab+Tram',
            'trametinib': 'Dab+Tram',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Pembrolizumab': {'hr': 0.57, 'lo': 0.43, 'hi': 0.74, 'source': 'KEYNOTE-054, Eggermont NEJM 2018'},
            'Dab+Tram': {'hr': 0.47, 'lo': 0.39, 'hi': 0.58, 'source': 'COMBI-AD, Long NEJM 2017'},
        },
        'published_ranking': ['Dab+Tram', 'Pembrolizumab', 'Placebo'],
    },

    # -- Topic 9: 2L DLBCL CAR-T EFS --
    # 3 CAR-T vs SOC trials. Includes negative trial (BELINDA) for diversity.
    {
        'name': '2L DLBCL CAR-T EFS',
        'reference_nma': 'Individual trial publications: ZUMA-7, TRANSFORM, BELINDA',
        'pico': {
            'P': 'Adults with relapsed/refractory large B-cell lymphoma after first-line therapy',
            'I': 'CAR-T cell therapy (axi-cel, liso-cel, tisa-cel)',
            'C': 'Standard of care (salvage chemo + transplant)',
            'O': 'Event-free survival',
        },
        'trials': [
            {'nctId': 'NCT03391466', 'pmid': '34891224', 'title': 'ZUMA-7 (Axi-cel vs SOC 2L DLBCL)',
             'authors': 'Locke FL', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT03575351', 'pmid': '35717989', 'title': 'TRANSFORM (Liso-cel vs SOC 2L LBCL)',
             'authors': 'Kamdar M', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT03570892', 'pmid': '34904798', 'title': 'BELINDA (Tisa-cel vs SOC 2L LBCL)',
             'authors': 'Bishop MR', 'year': '2022', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'event-free',
        'alt_keywords': ['efs', 'event free', 'progression', 'relapse'],
        'effect_type': 'HR',
        'common_comparator': 'SOC',
        'norm_map': {
            'axicabtagene': 'Axi-cel',
            'axi-cel': 'Axi-cel',
            'lisocabtagene': 'Liso-cel',
            'liso-cel': 'Liso-cel',
            'tisagenlecleucel': 'Tisa-cel',
            'tisa-cel': 'Tisa-cel',
            'standard': 'SOC',
            'salvage': 'SOC',
            'investigator': 'SOC',
            'control': 'SOC',
            'placebo': 'SOC',
        },
        'expect_favor_treatment': None,  # BELINDA is genuinely negative (HR 1.07), mixed direction
        'published_hrs': {
            'Axi-cel': {'hr': 0.40, 'lo': 0.31, 'hi': 0.51, 'source': 'ZUMA-7, Locke NEJM 2022'},
            'Liso-cel': {'hr': 0.35, 'lo': 0.23, 'hi': 0.53, 'source': 'TRANSFORM, Kamdar Lancet 2022'},
            'Tisa-cel': {'hr': 1.07, 'lo': 0.82, 'hi': 1.40, 'source': 'BELINDA, Bishop NEJM 2022'},
        },
        'published_ranking': ['Liso-cel', 'Axi-cel', 'SOC', 'Tisa-cel'],
    },

    # -- Topic 10: 1L ESCC ICI+Chemo OS --
    # 3 ICI+chemo trials vs chemo in esophageal squamous cell carcinoma
    {
        'name': '1L ESCC ICI+Chemo OS',
        'reference_nma': 'Individual trial publications: KEYNOTE-590, CheckMate-648, RATIONALE-306',
        'pico': {
            'P': 'Unresectable advanced or metastatic esophageal squamous cell carcinoma, first-line',
            'I': 'ICI plus chemotherapy',
            'C': 'Chemotherapy alone',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT03189719', 'pmid': '34454674', 'title': 'KEYNOTE-590 (Pembro+Chemo 1L esophageal)',
             'authors': 'Sun JM', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT03143153', 'pmid': '35108470', 'title': 'CheckMate-648 (Nivo+Chemo 1L ESCC)',
             'authors': 'Doki Y', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT03783442', 'pmid': '37080222', 'title': 'RATIONALE-306 (Tislelizumab+Chemo 1L ESCC)',
             'authors': 'Xu J', 'year': '2023', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'alt_keywords': ['survival', 'death', 'os'],
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            'pembrolizumab': 'Pembrolizumab',
            'ipilimumab': 'Nivo+Ipi',
            'nivolumab': 'Nivolumab',
            'tislelizumab': 'Tislelizumab',
            'chemotherapy': 'Chemo',
            'placebo': 'Chemo',
            'cisplatin': 'Chemo',
            'fluorouracil': 'Chemo',
            '5-fu': 'Chemo',
            'paclitaxel': 'Chemo',
            'control': 'Chemo',
            'soc': 'Chemo',
        },
        'expect_favor_treatment': True,
        # Using overall-population (ITT) HRs consistently for all trials
        # KN-590: ITT HR 0.73 (95% CI); CM-648: overall-pop HRs (99.1%/98.2% CIs from hierarchical testing)
        'published_hrs': {
            'Pembrolizumab': {'hr': 0.73, 'lo': 0.62, 'hi': 0.86, 'source': 'KEYNOTE-590 ITT all-randomised, Sun JM Lancet 2021'},
            'Nivolumab': {'hr': 0.74, 'lo': 0.58, 'hi': 0.96, 'source': 'CheckMate-648 Nivo+Chemo overall-pop, Doki NEJM 2022'},
            'Nivo+Ipi': {'hr': 0.78, 'lo': 0.62, 'hi': 0.98, 'source': 'CheckMate-648 Nivo+Ipi overall-pop, Doki NEJM 2022'},
            'Tislelizumab': {'hr': 0.66, 'lo': 0.54, 'hi': 0.80, 'source': 'RATIONALE-306 overall-pop, Xu JAMA 2023'},
        },
        'published_ranking': ['Tislelizumab', 'Pembrolizumab', 'Nivolumab', 'Nivo+Ipi', 'Chemo'],
    },

    # -- Topic 11: Adjuvant NSCLC DFS --
    # 3 trials: ICIs and targeted therapy. Wide dynamic range (ADAURA HR 0.17).
    {
        'name': 'Adjuvant NSCLC DFS',
        'reference_nma': 'Individual trial publications: IMpower010, PEARLS/KN-091, ADAURA',
        'pico': {
            'P': 'Resected stage IB-IIIA non-small cell lung cancer',
            'I': 'Adjuvant immune checkpoint inhibitor or targeted therapy',
            'C': 'Placebo or best supportive care',
            'O': 'Disease-free survival',
        },
        'trials': [
            {'nctId': 'NCT02486718', 'pmid': '34555333', 'title': 'IMpower010 (Atezolizumab adj NSCLC)',
             'authors': 'Felip E', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT02504372', 'pmid': '36108662', 'title': 'PEARLS/KN-091 (Pembrolizumab adj NSCLC)',
             'authors': "O'Brien M", 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT02511106', 'pmid': '32955177', 'title': 'ADAURA (Osimertinib adj EGFR-mutant NSCLC)',
             'authors': 'Wu YL', 'year': '2020', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'disease-free',
        'alt_keywords': ['dfs', 'disease free', 'recurrence', 'relapse'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'atezolizumab': 'Atezolizumab',
            'pembrolizumab': 'Pembrolizumab',
            'osimertinib': 'Osimertinib',
            'placebo': 'Placebo',
            'best supportive': 'Placebo',
            'bsc': 'Placebo',
            'control': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Atezolizumab': {'hr': 0.81, 'lo': 0.67, 'hi': 0.99, 'source': 'IMpower010 II-IIIA, Felip Lancet 2021'},
            'Pembrolizumab': {'hr': 0.76, 'lo': 0.63, 'hi': 0.91, 'source': 'PEARLS/KN-091, O\'Brien Ann Oncol 2022'},
            # ADAURA IB-IIIA overall: HR 0.20 (99.12% CI 0.14-0.30) at 24 months, Wu NEJM 2020
            # CT.gov may report updated 5-year DFS (~0.27 for IB-IIIA) — expect some discrepancy
            'Osimertinib': {'hr': 0.20, 'lo': 0.14, 'hi': 0.30, 'source': 'ADAURA IB-IIIA ITT, Wu NEJM 2020 (99.12% CI)'},
        },
        'published_ranking': ['Osimertinib', 'Pembrolizumab', 'Atezolizumab', 'Placebo'],
    },

    # -- Topic 12: nmCRPC AR Pathway Inhibitors (MFS) --
    # SPARTAN, PROSPER, ARAMIS: all AR inhibitors vs Placebo in non-metastatic CRPC
    {
        'name': 'nmCRPC AR Pathway Inhibitors (MFS)',
        'pico': {
            'P': 'Men with high-risk non-metastatic castration-resistant prostate cancer',
            'I': 'AR pathway inhibitor (apalutamide, enzalutamide, or darolutamide)',
            'C': 'Placebo + ADT',
            'O': 'Metastasis-free survival',
        },
        'trials': [
            {'nctId': 'NCT01946204', 'pmid': '29420164', 'title': 'SPARTAN (Apalutamide nmCRPC)',
             'authors': 'Smith MR', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT02003924', 'pmid': '29949494', 'title': 'PROSPER (Enzalutamide nmCRPC)',
             'authors': 'Hussain M', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT02200614', 'pmid': '30763142', 'title': 'ARAMIS (Darolutamide nmCRPC)',
             'authors': 'Fizazi K', 'year': '2019', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'metastasis',
        'alt_keywords': ['metastasis-free', 'mfs', 'radiographic progression', 'distant metastasis'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'apalutamide': 'Apalutamide',
            'arn-509': 'Apalutamide',
            'enzalutamide': 'Enzalutamide',
            'mdv3100': 'Enzalutamide',
            'darolutamide': 'Darolutamide',
            'odm-201': 'Darolutamide',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Apalutamide': {'hr': 0.28, 'lo': 0.23, 'hi': 0.35, 'source': 'SPARTAN, Smith NEJM 2018'},
            'Enzalutamide': {'hr': 0.29, 'lo': 0.24, 'hi': 0.35, 'source': 'PROSPER, Hussain NEJM 2018'},
            'Darolutamide': {'hr': 0.41, 'lo': 0.34, 'hi': 0.50, 'source': 'ARAMIS, Fizazi NEJM 2019'},
        },
        'published_ranking': ['Apalutamide', 'Enzalutamide', 'Darolutamide', 'Placebo'],
    },

    # -- Topic 13: 1L ES-SCLC ICI+Chemo OS --
    # IMpower133 (atezolizumab), CASPIAN (durvalumab) vs Chemo
    {
        'name': '1L ES-SCLC ICI+Chemo OS',
        'pico': {
            'P': 'Patients with untreated extensive-stage small cell lung cancer',
            'I': 'ICI + platinum-etoposide (atezolizumab or durvalumab)',
            'C': 'Platinum-etoposide chemotherapy alone',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT02763579', 'pmid': '30280641', 'title': 'IMpower133 (Atezolizumab ES-SCLC)',
             'authors': 'Horn L', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT03043872', 'pmid': '31590988', 'title': 'CASPIAN (Durvalumab ES-SCLC)',
             'authors': 'Paz-Ares L', 'year': '2019', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'alt_keywords': ['survival', 'death', 'os'],
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            'atezolizumab': 'Atezolizumab',
            'mpdl3280a': 'Atezolizumab',
            'durvalumab': 'Durvalumab',
            'medi4736': 'Durvalumab',
            'd + ep': 'Durvalumab',          # CASPIAN label "Global Cohort: D + EP"
            'carboplatin': 'Chemo',
            'cisplatin': 'Chemo',
            'etoposide': 'Chemo',
            'placebo': 'Chemo',
            'control': 'Chemo',
            'chemotherapy': 'Chemo',
            'standard': 'Chemo',
            'global cohort: ep': 'Chemo',    # CASPIAN comparator label
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Atezolizumab': {'hr': 0.70, 'lo': 0.54, 'hi': 0.91, 'source': 'IMpower133, Horn NEJM 2018'},
            'Durvalumab': {'hr': 0.73, 'lo': 0.59, 'hi': 0.91, 'source': 'CASPIAN, Paz-Ares Lancet 2019'},
        },
        'published_ranking': ['Atezolizumab', 'Durvalumab', 'Chemo'],
    },

    # -- Topic 14: 1L Biliary Tract ICI+GemCis OS --
    # TOPAZ-1 (durvalumab), KEYNOTE-966 (pembrolizumab) vs GemCis
    {
        'name': '1L Biliary Tract ICI+GemCis OS',
        'pico': {
            'P': 'Patients with advanced/unresectable biliary tract cancer',
            'I': 'ICI + gemcitabine-cisplatin (durvalumab or pembrolizumab)',
            'C': 'Placebo + gemcitabine-cisplatin',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT03875235', 'pmid': '38319896', 'title': 'TOPAZ-1 (Durvalumab BTC)',
             'authors': 'Oh DY', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT04003636', 'pmid': '37075781', 'title': 'KEYNOTE-966 (Pembrolizumab BTC)',
             'authors': 'Kelley RK', 'year': '2023', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'alt_keywords': ['survival', 'death', 'os'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'durvalumab': 'Durvalumab',
            'medi4736': 'Durvalumab',
            'pembrolizumab': 'Pembrolizumab',
            'mk-3475': 'Pembrolizumab',
            'placebo': 'Placebo',
            'gemcitabine': 'Placebo',
            'cisplatin': 'Placebo',
            'control': 'Placebo',
        },
        'expect_favor_treatment': True,
        'published_hrs': {
            'Durvalumab': {'hr': 0.80, 'lo': 0.66, 'hi': 0.97, 'source': 'TOPAZ-1, Oh NEJM EvidLive 2022'},
            'Pembrolizumab': {'hr': 0.83, 'lo': 0.72, 'hi': 0.95, 'source': 'KEYNOTE-966, Kelley Lancet 2023'},
        },
        'published_ranking': ['Durvalumab', 'Pembrolizumab', 'Placebo'],
    },
]


# ===================================================================
# CONCORDANCE ANALYSIS FUNCTIONS
# ===================================================================

def compute_concordance(extracted_hrs, published_hrs):
    """Compare extracted vs published HRs. Returns concordance metrics."""
    pairs = []
    for drug, pub in published_hrs.items():
        ext = extracted_hrs.get(drug)
        if ext is not None and pub.get('hr') is not None:
            pairs.append({
                'drug': drug,
                'extracted_hr': ext,
                'published_hr': pub['hr'],
                'pub_lo': pub.get('lo'),
                'pub_hi': pub.get('hi'),
                'log_diff': abs(math.log(ext) - math.log(pub['hr'])),
                'pct_diff': abs(ext - pub['hr']) / pub['hr'] * 100,
                'within_pub_ci': (pub.get('lo', 0) <= ext <= pub.get('hi', 999)) if pub.get('lo') else None,
            })

    if not pairs:
        return {'n_compared': 0, 'pairs': []}

    log_diffs = [p['log_diff'] for p in pairs]
    pct_diffs = [p['pct_diff'] for p in pairs]
    n_within_ci = sum(1 for p in pairs if p.get('within_pub_ci'))

    # Pearson correlation on log-HR scale
    ext_logs = [math.log(p['extracted_hr']) for p in pairs]
    pub_logs = [math.log(p['published_hr']) for p in pairs]
    n = len(pairs)
    if n >= 3:
        mean_e = sum(ext_logs) / n
        mean_p = sum(pub_logs) / n
        cov = sum((e - mean_e) * (p - mean_p) for e, p in zip(ext_logs, pub_logs)) / n
        var_e = sum((e - mean_e) ** 2 for e in ext_logs) / n
        var_p = sum((p - mean_p) ** 2 for p in pub_logs) / n
        r = cov / (math.sqrt(var_e * var_p)) if var_e > 0 and var_p > 0 else None
    else:
        r = None

    # Rank concordance (Spearman)
    ext_rank = sorted(range(n), key=lambda i: pairs[i]['extracted_hr'])
    pub_rank = sorted(range(n), key=lambda i: pairs[i]['published_hr'])
    ext_ranks = [0] * n
    pub_ranks = [0] * n
    for rank, idx in enumerate(ext_rank):
        ext_ranks[idx] = rank
    for rank, idx in enumerate(pub_rank):
        pub_ranks[idx] = rank
    d_sq = sum((er - pr) ** 2 for er, pr in zip(ext_ranks, pub_ranks))
    spearman = 1 - 6 * d_sq / (n * (n ** 2 - 1)) if n >= 3 else None

    return {
        'n_compared': n,
        'pairs': pairs,
        'mae_log_hr': sum(log_diffs) / n,
        'max_log_diff': max(log_diffs),
        'mae_pct': sum(pct_diffs) / n,
        'max_pct_diff': max(pct_diffs),
        'n_within_pub_ci': n_within_ci,
        'pearson_r': r,
        'spearman_rho': spearman,
    }


def compute_rank_concordance(our_pscores, published_ranking):
    """Compare P-score ranking vs published NMA ranking."""
    our_sorted = sorted(our_pscores.items(), key=lambda x: -x[1])
    our_ranking = [name for name, _ in our_sorted]

    # Only compare drugs present in both
    common = [d for d in our_ranking if d in published_ranking]
    if len(common) < 2:
        return None

    our_order = [common.index(d) if d in common else 999 for d in our_ranking if d in common]
    pub_order = [published_ranking.index(d) for d in common]

    n = len(common)
    # Kendall's tau (count concordant/discordant pairs)
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            our_d = our_order[i] - our_order[j]
            pub_d = pub_order[i] - pub_order[j]
            if our_d * pub_d > 0:
                concordant += 1
            elif our_d * pub_d < 0:
                discordant += 1

    total = concordant + discordant
    tau = (concordant - discordant) / total if total > 0 else None

    return {
        'our_ranking': [d for d in our_ranking if d in common],
        'published_ranking': [d for d in published_ranking if d in common],
        'n_common': n,
        'concordant_pairs': concordant,
        'discordant_pairs': discordant,
        'kendall_tau': tau,
    }


# ===================================================================
# MAIN TEST RUNNER (extraction + NMA + concordance analysis)
# ===================================================================

def run_topic(driver, topic, topic_idx):
    """Run a single topic and return result with concordance metrics."""
    result = {
        'name': topic['name'],
        'status': 'UNKNOWN',
        'n_trials_input': len(topic['trials']),
        'n_trials_extracted': 0,
        'n_outcomes_extracted': 0,
        'n_outcomes_selected': 0,
        'n_studies_in_table': 0,
        'nma_treatments': 0,
        'nma_edges': 0,
        'pscores': {},
        'issues': [],
        'drug_vs_ref': {},
        'raw_treatment_names': [],
        'concordance': None,
        'rank_concordance': None,
    }

    try:
        driver.get(FILE_URL)
        driver.execute_script("""
            try { localStorage.clear(); sessionStorage.clear(); } catch(e) {}
            try { indexedDB.deleteDatabase('MetaSprintNMA'); } catch(e) {}
        """)
        time.sleep(0.5)
        driver.get(FILE_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
        time.sleep(1)
        try:
            driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except Exception:
            pass

        n_existing = driver.execute_script(
            "return typeof extractedStudies !== 'undefined' ? extractedStudies.length : -1")
        if n_existing > 0:
            driver.execute_script("extractedStudies.length = 0;")

        # Step 1: Create project
        pico = topic['pico']
        driver.execute_script(f"""
            var nameInput = document.getElementById('projectName');
            if (nameInput) {{ nameInput.value = {json.dumps(topic['name'])}; nameInput.dispatchEvent(new Event('input')); }}
            var pI = document.getElementById('picoP');
            var iI = document.getElementById('picoI');
            var cI = document.getElementById('picoC');
            var oI = document.getElementById('picoO');
            if(pI) pI.value = {json.dumps(pico['P'])};
            if(iI) iI.value = {json.dumps(pico['I'])};
            if(cI) cI.value = {json.dumps(pico['C'])};
            if(oI) oI.value = {json.dumps(pico['O'])};
            if(typeof createProject==='function') createProject();
        """)
        time.sleep(0.5)

        # Step 2: Inject + extract
        trials_json = json.dumps(topic['trials'])
        driver.execute_script(f"""
            switchPhase('search');
            searchResultsCache = {trials_json};
            var aeRow = document.getElementById('autoExtractRow');
            if (aeRow) aeRow.style.display = 'block';
        """)
        time.sleep(0.3)

        driver.execute_script("runAutoExtract()")
        for tick in range(90):
            time.sleep(2)
            running = driver.execute_script("return typeof _autoExtractRunning !== 'undefined' ? _autoExtractRunning : false")
            if not running:
                break
        else:
            result['issues'].append('EXTRACTION_TIMEOUT: Polling exhausted 90 ticks (180s) without completion')

        n_trials = driver.execute_script("return typeof _extractionResults !== 'undefined' ? _extractionResults.length : 0")
        total_outcomes = driver.execute_script(
            "return typeof _extractionResults !== 'undefined' ? _extractionResults.reduce(function(s,t){return s+(t.outcomes?t.outcomes.length:0)},0) : 0")
        result['n_trials_extracted'] = n_trials
        result['n_outcomes_extracted'] = total_outcomes

        if n_trials == 0 or total_outcomes == 0:
            result['status'] = 'EXTRACT_FAIL'
            return result

        # Step 3: Select outcomes
        outcome_kw = topic['outcome_keyword']
        alt_keywords = topic.get('alt_keywords', [])
        effect_type = topic['effect_type']
        all_keywords = [outcome_kw] + alt_keywords

        driver.execute_script(f"""
            var keywords = {json.dumps(all_keywords)};
            var et = {json.dumps(effect_type)};
            for (var t of _extractionResults) {{
                for (var o of (t.outcomes||[])) o.checked = false;
            }}
            for (var t of _extractionResults) {{
                var matches = [];
                for (var kw of keywords) {{
                    kw = kw.toLowerCase();
                    for (var o of (t.outcomes||[])) {{
                        if (o.effectType !== et) continue;
                        var title = (o.outcomeTitle || '').toLowerCase();
                        if (title.indexOf(kw) >= 0) matches.push(o);
                    }}
                    if (matches.length > 0) break;
                }}
                if (matches.length === 0) {{
                    for (var o of (t.outcomes||[])) {{
                        if (o.effectType === et) matches.push(o);
                    }}
                }}
                if (matches.length > 0) {{
                    var best = matches[0];
                    for (var m of matches) {{
                        if (m.isPrimary && !best.isPrimary) best = m;
                    }}
                    best.checked = true;
                }}
            }}
            if (typeof renderExtractionReview === 'function') renderExtractionReview();
        """)
        time.sleep(0.3)

        n_selected = driver.execute_script("""
            var c = 0;
            for (var t of _extractionResults) {
                for (var o of (t.outcomes||[])) { if (o.checked) c++; }
            }
            return c;
        """)
        result['n_outcomes_selected'] = n_selected

        if n_selected < 2:
            result['status'] = 'TOO_FEW'
            return result

        # Step 4: Accept + normalize
        driver.execute_script("acceptExtractedStudies()")
        time.sleep(0.5)
        n_studies = driver.execute_script("return typeof extractedStudies !== 'undefined' ? extractedStudies.length : 0")
        result['n_studies_in_table'] = n_studies

        if n_studies < 2:
            result['status'] = 'ACCEPT_FAIL'
            return result

        raw_names = json.loads(driver.execute_script("""
            return JSON.stringify(extractedStudies.map(function(s) {
                return {t1: s.treatment1, t2: s.treatment2, nct: s.nctId};
            }));
        """))
        result['raw_treatment_names'] = raw_names

        norm_map = topic['norm_map']
        norm_map_json = json.dumps(norm_map)
        driver.execute_script(f"""
            var nmap = {norm_map_json};
            function normT(name) {{
                var n = (name || '').trim();
                var lo = n.toLowerCase();
                for (var key in nmap) {{
                    if (lo.indexOf(key.toLowerCase()) >= 0) return nmap[key];
                }}
                return n;
            }}
            for (var s of extractedStudies) {{
                s.treatment1 = normT(s.treatment1);
                s.treatment2 = normT(s.treatment2);
                s.effectType = {json.dumps(effect_type)};
                s.outcomeId = {json.dumps(topic['outcome_keyword'])};
                s.timepoint = 'Primary analysis';
            }}
        """)

        # Deduplicate
        driver.execute_script("""
            var seen = {};
            var keep = [];
            for (var s of extractedStudies) {
                var key = s.nctId || s.authorYear;
                if (!seen[key]) { seen[key] = true; keep.push(s); }
            }
            extractedStudies.length = 0;
            for (var s of keep) extractedStudies.push(s);
        """)

        # Step 5: Run NMA
        engine_result = json.loads(driver.execute_script("""
            try {
                var valid = extractedStudies.filter(function(s) {
                    return s.effectEstimate !== null && s.lowerCI !== null && s.upperCI !== null;
                });
                if (valid.length < 2) return JSON.stringify({error: 'Need >=2 valid studies, got ' + valid.length});

                var network = buildNetworkGraph(valid);
                if (!network || network.nE === 0) return JSON.stringify({error: 'Empty network'});

                if (network.components && network.components.length > 1) {
                    return JSON.stringify({error: 'Disconnected: ' + network.components.length + ' components'});
                }

                var result = runFrequentistNMA(network, 0.95, {tau2Method: 'DL'});
                return JSON.stringify({
                    ok: true,
                    nT: result.nT, nE: result.nE,
                    tau2: result.tau2, I2: result.I2global,
                    treatments: result.treatments,
                    ref: result.refTreatment,
                    isRatio: result.isRatio,
                    d: Array.from(result.d || []),
                    pscores: result.pscores,
                    leagueTable: (result.leagueTable || []).slice(0, 100)
                });
            } catch(e) {
                return JSON.stringify({error: e.message});
            }
        """))

        if engine_result.get('error'):
            result['issues'].append(f'NMA_ERROR: {engine_result["error"]}')
            result['status'] = 'NMA_FAIL'
            return result

        result['nma_treatments'] = engine_result['nT']
        result['nma_edges'] = engine_result['nE']

        # Extract P-scores
        pscores = engine_result.get('pscores', {})
        treatments = engine_result.get('treatments', [])
        scored = []
        for k in pscores:
            idx = int(k)
            if idx < len(treatments):
                scored.append((treatments[idx], pscores[k]))
        scored.sort(key=lambda x: -x[1])
        result['pscores'] = {name: ps for name, ps in scored}

        # Extract drug vs comparator HRs from league table
        comp = topic.get('common_comparator', '').lower()
        lt = engine_result.get('leagueTable', [])
        is_ratio = engine_result.get('isRatio', False)
        extracted_hrs = {}

        for entry in lt:
            t1 = entry.get('t1', '')
            t2 = entry.get('t2', '')
            eff = entry.get('effect', entry.get('eff', None))
            lo = entry.get('lo')
            hi = entry.get('hi')
            if not isinstance(eff, (int, float)):
                continue
            # Use exact match for comparator (substring fails when comp like "ai" is in "palbociclib+ai")
            if t2.lower() == comp and t1.lower() != comp:
                if is_ratio:
                    try:
                        hr = math.exp(eff)
                        hr_lo = math.exp(lo) if isinstance(lo, (int, float)) else None
                        hr_hi = math.exp(hi) if isinstance(hi, (int, float)) else None
                    except (OverflowError, ValueError):
                        continue
                    extracted_hrs[t1] = hr
                    result['drug_vs_ref'][t1] = {'hr': hr, 'lo': hr_lo, 'hi': hr_hi}

        # Step 6: Concordance analysis
        published_hrs = topic.get('published_hrs', {})
        if published_hrs and extracted_hrs:
            result['concordance'] = compute_concordance(extracted_hrs, published_hrs)

        published_ranking = topic.get('published_ranking', [])
        if published_ranking and result['pscores']:
            result['rank_concordance'] = compute_rank_concordance(result['pscores'], published_ranking)

        result['status'] = 'PASS'

    except Exception as e:
        result['status'] = 'EXCEPTION'
        result['issues'].append(f'EXCEPTION: {str(e)}')
        traceback.print_exc()

    return result


def main():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1200')
    opts.add_argument('--disable-web-security')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(5)

    n_topics = len(TOPICS)
    results = []
    all_pairs = []

    try:
        print('=' * 90)
        print(f'NMA CONCORDANCE VALIDATION: {n_topics} TOPICS vs PUBLISHED NMAs')
        print('Comparing automated CT.gov extraction + NMA engine against peer-reviewed results')
        print('=' * 90)

        for i, topic in enumerate(TOPICS):
            print(f'\n{"="*90}')
            print(f'TOPIC {i+1}/{n_topics}: {topic["name"]}')
            print(f'Reference: {topic.get("reference_nma", "N/A")}')
            print(f'Trials: {len(topic["trials"])} | Outcome: {topic["outcome_keyword"]} ({topic["effect_type"]})')
            print(f'{"="*90}')

            result = run_topic(driver, topic, i)
            results.append(result)

            print(f'\n  Status: {result["status"]}')
            print(f'  Extracted: {result["n_trials_extracted"]} trials, {result["n_outcomes_extracted"]} outcomes')
            print(f'  NMA: {result["nma_treatments"]} treatments, {result["nma_edges"]} edges')

            if result['raw_treatment_names']:
                print(f'  Raw names:')
                for rn in result['raw_treatment_names']:
                    print(f'    {rn.get("nct","?")}: "{rn["t1"]}" vs "{rn["t2"]}"')

            if result['pscores']:
                print(f'  P-score ranking:')
                for name, ps in sorted(result['pscores'].items(), key=lambda x: -x[1]):
                    print(f'    {name:30s}: {ps:.3f}')

            # CONCORDANCE RESULTS
            conc = result.get('concordance')
            if conc and conc['n_compared'] > 0:
                print(f'\n  CONCORDANCE vs PUBLISHED ({conc["n_compared"]} comparisons):')
                print(f'  {"Drug":<25} {"Extracted":>10} {"Published":>10} {"Diff%":>8} {"|logHR|":>8} {"In CI?":>7}')
                print(f'  {"-"*25} {"-"*10} {"-"*10} {"-"*8} {"-"*8} {"-"*7}')
                for p in conc['pairs']:
                    ci_str = 'YES' if p.get('within_pub_ci') else 'no'
                    print(f'  {p["drug"]:<25} {p["extracted_hr"]:>10.3f} {p["published_hr"]:>10.3f} '
                          f'{p["pct_diff"]:>7.1f}% {p["log_diff"]:>8.4f} {ci_str:>7}')

                print(f'\n  MAE (log-HR scale): {conc["mae_log_hr"]:.4f}')
                print(f'  MAE (% scale):      {conc["mae_pct"]:.1f}%')
                print(f'  Within pub CI:      {conc["n_within_pub_ci"]}/{conc["n_compared"]}')
                if conc.get('pearson_r') is not None:
                    print(f'  Pearson r (logHR):  {conc["pearson_r"]:.4f}')
                if conc.get('spearman_rho') is not None:
                    print(f'  Spearman rho:       {conc["spearman_rho"]:.4f}')

                all_pairs.extend(conc['pairs'])

            # RANK CONCORDANCE
            rc = result.get('rank_concordance')
            if rc:
                print(f'\n  RANK CONCORDANCE:')
                print(f'    Our ranking:       {" > ".join(rc["our_ranking"])}')
                print(f'    Published ranking: {" > ".join(rc["published_ranking"])}')
                if rc.get('kendall_tau') is not None:
                    print(f'    Kendall tau:       {rc["kendall_tau"]:.3f}')

            if result['issues']:
                print(f'  Issues: {result["issues"]}')

        # ═══════════════════════════════════════════════════
        # GLOBAL CONCORDANCE REPORT
        # ═══════════════════════════════════════════════════
        print(f'\n\n{"="*90}')
        print(f'GLOBAL CONCORDANCE REPORT ({n_topics} TOPICS, {len(all_pairs)} COMPARISONS)')
        print(f'{"="*90}')

        pass_count = sum(1 for r in results if r['status'] == 'PASS')
        print(f'\n  Pipeline: {pass_count}/{n_topics} topics extracted + NMA completed')

        if all_pairs:
            all_log_diffs = [p['log_diff'] for p in all_pairs]
            all_pct_diffs = [p['pct_diff'] for p in all_pairs]
            n_within = sum(1 for p in all_pairs if p.get('within_pub_ci'))

            print(f'\n  OVERALL HR CONCORDANCE ({len(all_pairs)} drug-vs-comparator HRs):')
            print(f'    MAE (log-HR scale):    {sum(all_log_diffs)/len(all_log_diffs):.4f}')
            print(f'    Max |log-HR diff|:     {max(all_log_diffs):.4f}')
            print(f'    MAE (% scale):         {sum(all_pct_diffs)/len(all_pct_diffs):.1f}%')
            print(f'    Max % difference:      {max(all_pct_diffs):.1f}%')
            print(f'    Within published CI:   {n_within}/{len(all_pairs)} ({100*n_within/len(all_pairs):.0f}%)')

            # Global Pearson r
            ext_logs = [math.log(p['extracted_hr']) for p in all_pairs]
            pub_logs = [math.log(p['published_hr']) for p in all_pairs]
            n = len(all_pairs)
            mean_e = sum(ext_logs) / n
            mean_p = sum(pub_logs) / n
            cov = sum((e - mean_e) * (p - mean_p) for e, p in zip(ext_logs, pub_logs)) / n
            var_e = sum((e - mean_e) ** 2 for e in ext_logs) / n
            var_p = sum((p - mean_p) ** 2 for p in pub_logs) / n
            global_r = cov / (math.sqrt(var_e * var_p)) if var_e > 0 and var_p > 0 else None
            if global_r is not None:
                print(f'    Pearson r (logHR):     {global_r:.4f}')

            # Threshold checks
            n_close = sum(1 for p in all_pairs if p['pct_diff'] < 10)
            n_very_close = sum(1 for p in all_pairs if p['pct_diff'] < 5)
            print(f'\n    Within 5% of published:  {n_very_close}/{len(all_pairs)}')
            print(f'    Within 10% of published: {n_close}/{len(all_pairs)}')

            # Per-pair detail
            print(f'\n  ALL COMPARISONS (sorted by |diff|):')
            print(f'  {"Topic":<35} {"Drug":<22} {"Ext HR":>8} {"Pub HR":>8} {"Diff%":>7} {"In CI":>6}')
            print(f'  {"-"*35} {"-"*22} {"-"*8} {"-"*8} {"-"*7} {"-"*6}')
            for r_idx, r in enumerate(results):
                conc = r.get('concordance')
                if not conc:
                    continue
                for p in sorted(conc.get('pairs', []), key=lambda x: x['pct_diff']):
                    ci = 'YES' if p.get('within_pub_ci') else 'no'
                    print(f'  {r["name"][:35]:<35} {p["drug"][:22]:<22} '
                          f'{p["extracted_hr"]:>8.3f} {p["published_hr"]:>8.3f} '
                          f'{p["pct_diff"]:>6.1f}% {ci:>6}')

    finally:
        driver.quit()

    # Concordance quality assertions
    concordance_ok = True
    if not all_pairs:
        global_r = None
    if all_pairs:
        n_within = sum(1 for p in all_pairs if p.get('within_pub_ci'))
        pct_within = 100 * n_within / len(all_pairs)
        avg_pct_diff = sum(p['pct_diff'] for p in all_pairs) / len(all_pairs)

        print(f'\n  QUALITY GATES:')
        # Gate 1: >=80% of extracted HRs within published CI
        gate1 = pct_within >= 80
        print(f'    Within published CI >= 80%:  {pct_within:.0f}% {"PASS" if gate1 else "FAIL"}')
        # Gate 2: Mean % difference < 15%
        gate2 = avg_pct_diff < 15
        print(f'    Mean % difference < 15%:     {avg_pct_diff:.1f}% {"PASS" if gate2 else "FAIL"}')
        # Gate 3: Pearson r >= 0.90 (if enough pairs)
        gate3 = global_r is not None and global_r >= 0.90
        print(f'    Pearson r >= 0.90:           {(f"{global_r:.4f}" if global_r else "N/A")} {"PASS" if gate3 else "FAIL"}')

        concordance_ok = gate1 and gate2 and gate3

    print(f'\n{"="*90}')
    print(f'CONCORDANCE VALIDATION {"COMPLETE" if (pass_count == n_topics and concordance_ok) else "FAILED"}')
    print(f'{"="*90}')
    sys.exit(0 if (pass_count == n_topics and concordance_ok) else 1)


if __name__ == '__main__':
    main()
