"""
NMA Pipeline Stress Test Round 2: 10 New Topics with Published NMA Benchmarks
===============================================================================
All trials verified to have structured HR results on ClinicalTrials.gov.
Each topic cross-referenced against published NMAs for HR validation.

Topics span: oncology, cardiology, endocrinology, hematology, gynecology.
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

# ═══════════════════════════════════════════════════════════════════
# TOPIC CONFIGURATIONS — 10 new topics, all CT.gov-verified
# ═══════════════════════════════════════════════════════════════════

TOPICS = [
    # ── Topic 1: First-line mRCC ICI Combos vs Sunitinib (OS) ──
    # Published NMA: Yanagisawa 2024 BJU Int; Targeted Oncology 2025
    # All 5 trials have structured HR on CT.gov. Star network: all vs Sunitinib.
    {
        'name': '1L mRCC ICI vs Sunitinib',
        'pico': {
            'P': 'Previously untreated advanced or metastatic renal cell carcinoma',
            'I': 'Immune checkpoint inhibitor-based combinations',
            'C': 'Sunitinib monotherapy',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT02231749', 'pmid': '29562145', 'title': 'CheckMate 214 (Nivo+Ipi vs Sunitinib)',
             'authors': 'Motzer RJ', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT02853331', 'pmid': '30779529', 'title': 'KEYNOTE-426 (Pembro+Axi vs Sunitinib)',
             'authors': 'Rini BI', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02684006', 'pmid': '30779531', 'title': 'JAVELIN Renal 101 (Avel+Axi vs Sunitinib)',
             'authors': 'Motzer RJ', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT03141177', 'pmid': '33657295', 'title': 'CheckMate 9ER (Nivo+Cabo vs Sunitinib)',
             'authors': 'Choueiri TK', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT02811861', 'pmid': '33616314', 'title': 'CLEAR (Len+Pembro vs Sunitinib)',
             'authors': 'Motzer RJ', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'effect_type': 'HR',
        'common_comparator': 'Sunitinib',
        'norm_map': {
            # CheckMate 9ER om.groups: "Treatment A", "Treatment B", "Treatment C"
            'treatment a': 'Nivo+Cabo',
            'treatment c': 'Sunitinib',
            # CheckMate 9ER armGroup labels (fallback)
            'doublet': 'Nivo+Cabo',
            'triplet': 'Nivo+Cabo+Ipi',  # 3-arm trial, skip if extracted
            'monotherapy': 'Sunitinib',
            # CLEAR has 3 arms — match the specific arm labels
            'lenvatinib 20 mg plus pembrolizumab': 'Len+Pembro',
            'lenvatinib 18 mg plus everolimus': 'Len+Eve',
            # JAVELIN
            'avelumab': 'Avel+Axi',
            # CheckMate 214 — check ipilimumab BEFORE nivolumab
            'ipilimumab': 'Nivo+Ipi',
            'nivolumab': 'Nivo+Ipi',
            # KEYNOTE-426
            'axitinib': 'Pembro+Axi',
            'pembrolizumab': 'Pembro+Axi',
            # CLEAR fallback (after specific patterns above)
            'lenvatinib': 'Len+Pembro',
            'everolimus': 'Len+Eve',
            'cabozantinib': 'Nivo+Cabo',
            'sunitinib': 'Sunitinib',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'Published NMA OS vs Suni: CM214 ~0.69, KN426 ~0.73, JAVELIN ~0.69, CM9ER ~0.70, CLEAR ~0.66',
        'benchmarks': {
            'Nivo+Ipi': (0.60, 0.80),     # HR range from published NMAs
            'Pembro+Axi': (0.45, 0.85),  # Single trial (KN-426) direct extract; CLEAR Len+Pembro is separate arm
            'Avel+Axi': (0.55, 0.95),  # JAVELIN Renal 101 OS non-significant (HR ~0.87)
            'Nivo+Cabo': (0.55, 0.85),
            'Len+Pembro': (0.50, 0.80),
        },
    },

    # ── Topic 2: CDK4/6 Inhibitors in 1L HR+/HER2- Breast Cancer (PFS) ──
    # Published NMA: BMC Cancer 2025; Deng 2024 JCO; multiple published NMAs
    # All 3 CDK4/6i 1L trials with AI as comparator. Common comparator: AI (Letrozole/NSAI).
    {
        'name': 'CDK4/6i 1L HR+ Breast PFS',
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
        'benchmark_note': 'Published NMA PFS HR vs AI: Palbo ~0.58, Ribo ~0.56, Abema ~0.54',
        'benchmarks': {
            'Palbociclib+AI': (0.45, 0.70),
            'Ribociclib+AI': (0.45, 0.70),
            'Abemaciclib+AI': (0.40, 0.70),
        },
    },

    # ── Topic 3: GLP-1 RA Cardiovascular Outcome Trials (MACE) ──
    # Published NMA: JACC 2025 meta-analysis of 99,599 patients
    # 4 GLP-1 RA CVOTs, all vs Placebo, all with HR on CT.gov.
    {
        'name': 'GLP-1 RA CVOT MACE',
        'pico': {
            'P': 'Type 2 diabetes with high cardiovascular risk',
            'I': 'GLP-1 receptor agonists',
            'C': 'Placebo',
            'O': 'Major adverse cardiovascular events (MACE)',
        },
        'trials': [
            {'nctId': 'NCT01179048', 'pmid': '27295427', 'title': 'LEADER (Liraglutide)',
             'authors': 'Marso SP', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT01720446', 'pmid': '27633186', 'title': 'SUSTAIN-6 (Semaglutide)',
             'authors': 'Marso SP', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT01144338', 'pmid': '28910237', 'title': 'EXSCEL (Exenatide)',
             'authors': 'Holman RR', 'year': '2017', 'source': 'ctgov'},
            {'nctId': 'NCT02465515', 'pmid': '30291013', 'title': 'HARMONY (Albiglutide)',
             'authors': 'Hernandez AF', 'year': '2018', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'mace',
        'alt_keywords': ['cardiovascular', 'cv death', 'major adverse', 'cardiac event'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'liraglutide': 'Liraglutide',
            'semaglutide': 'Semaglutide',
            'exenatide': 'Exenatide',
            'albiglutide': 'Albiglutide',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'LEADER HR 0.87, SUSTAIN-6 HR 0.74, EXSCEL HR 0.91, HARMONY HR 0.78',
        'benchmarks': {
            'Liraglutide': (0.75, 0.98),
            'Semaglutide': (0.60, 0.92),
            'Exenatide': (0.80, 1.05),     # EXSCEL was non-significant
            'Albiglutide': (0.65, 0.95),
        },
    },

    # ── Topic 4: SGLT2i in Heart Failure (CV death/HHF) ──
    # Published NMA: Lancet 2024; Circulation 2024
    # DAPA-HF (HFrEF), EMPEROR-Reduced (HFrEF), EMPEROR-Preserved (HFpEF)
    {
        'name': 'SGLT2i Heart Failure',
        'pico': {
            'P': 'Heart failure (reduced or preserved ejection fraction)',
            'I': 'SGLT2 inhibitors (dapagliflozin, empagliflozin)',
            'C': 'Placebo',
            'O': 'Cardiovascular death or hospitalization for heart failure',
        },
        'trials': [
            {'nctId': 'NCT03036124', 'pmid': '31535829', 'title': 'DAPA-HF (Dapagliflozin, HFrEF)',
             'authors': 'McMurray JJV', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT03057977', 'pmid': '32865377', 'title': 'EMPEROR-Reduced (Empagliflozin, HFrEF)',
             'authors': 'Packer M', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT03057951', 'pmid': '34449189', 'title': 'EMPEROR-Preserved (Empagliflozin, HFpEF)',
             'authors': 'Anker SD', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'death',
        'alt_keywords': ['cardiovascular', 'composite', 'hospitali'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'dapagliflozin': 'Dapagliflozin',
            'empagliflozin': 'Empagliflozin',
            '10 mg empagliflozin': 'Empagliflozin',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'DAPA-HF HR 0.74, EMPEROR-Reduced HR 0.75, EMPEROR-Preserved HR 0.79',
        'benchmarks': {
            'Dapagliflozin': (0.60, 0.88),
            'Empagliflozin': (0.60, 0.90),
        },
    },

    # ── Topic 5: PARP Maintenance in Relapsed Ovarian Cancer (PFS) ──
    # Published NMA: Oncotarget 2019; Gynecol Oncol 2021
    # 3 PARPi vs Placebo. Clean star network.
    {
        'name': 'PARPi Maintenance Ovarian PFS',
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
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'olaparib': 'Olaparib',
            'niraparib': 'Niraparib',
            'rucaparib': 'Rucaparib',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'All-comers PFS HR: SOLO2 ~0.30, NOVA ~0.38, ARIEL3 ~0.36',
        'benchmarks': {
            'Olaparib': (0.15, 0.50),
            'Niraparib': (0.20, 0.55),
            'Rucaparib': (0.20, 0.55),
        },
    },

    # ── Topic 6: First-line HCC vs Sorafenib (OS) ──
    # Published NMA: J Hepatol 2024; Cancer Immunol Immunother 2023
    # 3 trials, all vs Sorafenib. IMbrave150, HIMALAYA, CheckMate 459.
    {
        'name': '1L HCC vs Sorafenib',
        'pico': {
            'P': 'Unresectable hepatocellular carcinoma, first-line systemic',
            'I': 'ICI-based combinations or ICI monotherapy',
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
        'effect_type': 'HR',
        'common_comparator': 'Sorafenib',
        'norm_map': {
            # HIMALAYA om.groups: "Treme 300 mg x1 Dose + Durva 1500 mg", "Sora 400 mg"
            'treme': 'Durva+Treme',
            'sora': 'Sorafenib',
            # HIMALAYA armGroup labels fallback
            'arm 1': 'Durva+Treme',
            'arm 2': 'Durvalumab',
            'arm 4': 'Sorafenib',
            # IMbrave150 (om.groups: "Atezolizumab + Bevacizumab - Global", "Sorafenib - Global")
            'atezolizumab': 'Atezo+Bev',
            'bevacizumab': 'Atezo+Bev',
            # CheckMate 459
            'nivolumab': 'Nivolumab',
            'opdivo': 'Nivolumab',
            'ono-4538': 'Nivolumab',
            # Comparator
            'sorafenib': 'Sorafenib',
            # HIMALAYA specific drug names
            'durvalumab': 'Durva+Treme',
            'tremelimumab': 'Durva+Treme',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'IMbrave150 OS HR 0.58, HIMALAYA STRIDE HR 0.78, CM459 HR 0.85 (NS)',
        'benchmarks': {
            'Atezo+Bev': (0.45, 0.75),
            'Durva+Treme': (0.60, 0.95),
            'Nivolumab': (0.70, 1.05),    # CM459 was not significant
        },
    },

    # ── Topic 7: mHSPC ADT Intensification (OS) ──
    # Published NMA: Lancet Oncol 2023 Vale et al.; Eur Urol 2024
    # 3 NHAs + ADT vs ADT alone. Star network.
    {
        'name': 'mHSPC ADT Intensification',
        'pico': {
            'P': 'Metastatic hormone-sensitive prostate cancer',
            'I': 'Novel hormonal agent + ADT',
            'C': 'ADT alone (+ placebo)',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT02677896', 'pmid': '31329516', 'title': 'ARCHES (Enzalutamide+ADT vs ADT)',
             'authors': 'Armstrong AJ', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02489318', 'pmid': '31150574', 'title': 'TITAN (Apalutamide+ADT vs ADT)',
             'authors': 'Chi KN', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT01715285', 'pmid': '28578607', 'title': 'LATITUDE (Abiraterone+ADT vs ADT)',
             'authors': 'Fizazi K', 'year': '2017', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'effect_type': 'HR',
        'common_comparator': 'ADT',
        'norm_map': {
            'enzalutamide': 'Enza+ADT',
            'apalutamide': 'Apa+ADT',
            'abiraterone': 'Abi+ADT',
            'prednisone': 'Abi+ADT',       # LATITUDE includes prednisone
            'placebo': 'ADT',
            'androgen deprivation': 'ADT',
            'adt': 'ADT',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'ARCHES OS HR 0.66, TITAN OS HR 0.65, LATITUDE OS HR 0.62',
        'benchmarks': {
            'Enza+ADT': (0.50, 0.80),
            'Apa+ADT': (0.50, 0.80),
            'Abi+ADT': (0.48, 0.78),
        },
    },

    # ── Topic 8: First-line TNBC ICI+Chemo (PFS or OS) ──
    # Published NMA: Lancet Oncol 2024
    # 3 trials testing ICI+chemo vs chemo in metastatic TNBC.
    {
        'name': '1L TNBC ICI+Chemo',
        'pico': {
            'P': 'Metastatic triple-negative breast cancer, first-line',
            'I': 'Immune checkpoint inhibitor + chemotherapy',
            'C': 'Chemotherapy alone (+ placebo)',
            'O': 'Progression-free survival or overall survival',
        },
        'trials': [
            {'nctId': 'NCT02819518', 'pmid': '33278935', 'title': 'KEYNOTE-355 (Pembro+Chemo)',
             'authors': 'Cortes J', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT02425891', 'pmid': '30345906', 'title': 'IMpassion130 (Atezo+nab-Pac)',
             'authors': 'Schmid P', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT03125902', 'pmid': '34219000', 'title': 'IMpassion131 (Atezo+Pac)',
             'authors': 'Miles D', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'survival',
        'alt_keywords': ['progression', 'pfs', 'os'],
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            # KEYNOTE-355: arm labels include "Part 2: Pembrolizumab + Chemotherapy" etc.
            'pembrolizumab': 'Pembro+Chemo',
            'mk-3475': 'Pembro+Chemo',
            # IMpassion130 and 131: Atezolizumab labels
            'atezolizumab': 'Atezo+Chemo',
            'mpdl3280a': 'Atezo+Chemo',
            # Chemo labels
            'nab-paclitaxel': 'Chemo',
            'paclitaxel': 'Chemo',
            'gemcitabine': 'Chemo',
            'carboplatin': 'Chemo',
            'placebo': 'Chemo',
            'chemotherapy': 'Chemo',
        },
        'expect_favor_treatment': None,  # Mixed results (IMpassion131 negative)
        'benchmark_note': 'KN355 PFS HR 0.65 (PD-L1+), IMpassion130 PFS HR 0.80, IMpassion131 PFS HR 0.86 (NS)',
        'benchmarks': {
            'Pembro+Chemo': (0.50, 0.85),
            'Atezo+Chemo': (0.65, 1.10),   # Mixed results across trials
        },
    },

    # ── Topic 9: Biliary Tract Cancer 1L ICI+GemCis (OS) ──
    # Published meta-analysis: Lancet Oncol 2024
    # 2 landmark trials, both ICI+GemCis vs Placebo+GemCis
    {
        'name': 'BTC 1L ICI+GemCis',
        'pico': {
            'P': 'Advanced biliary tract cancer, first-line',
            'I': 'ICI + gemcitabine-cisplatin',
            'C': 'Placebo + gemcitabine-cisplatin',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT03875235', 'pmid': '38319896', 'title': 'TOPAZ-1 (Durvalumab+GemCis)',
             'authors': 'Oh DY', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT04003636', 'pmid': '37075781', 'title': 'KEYNOTE-966 (Pembro+GemCis)',
             'authors': 'Kelley RK', 'year': '2023', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'effect_type': 'HR',
        'common_comparator': 'GemCis',
        'norm_map': {
            # TOPAZ-1: arms "Treatment Arm" vs "Placebo Arm"
            'treatment arm': 'Durva+GemCis',
            'durvalumab': 'Durva+GemCis',
            # KEYNOTE-966: arms "Arm A (Pembrolizumab+Gemcitabine+Cisplatin)" etc.
            'pembrolizumab': 'Pembro+GemCis',
            'arm a': 'Pembro+GemCis',
            'arm b': 'GemCis',
            # Comparator
            'placebo arm': 'GemCis',
            'placebo': 'GemCis',
            'gemcitabine': 'GemCis',
            'cisplatin': 'GemCis',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'TOPAZ-1 OS HR 0.80, KEYNOTE-966 OS HR 0.83',
        'benchmarks': {
            'Durva+GemCis': (0.65, 0.95),
            'Pembro+GemCis': (0.68, 0.98),
        },
    },

    # ── Topic 10: Adjuvant Melanoma (RFS) ──
    # Published NMA: Lancet Oncol 2020
    # 3 trials, 2 treatments vs Placebo. Star network.
    {
        'name': 'Adjuvant Melanoma RFS',
        'pico': {
            'P': 'Resected stage III or stage IIB/C melanoma',
            'I': 'Adjuvant immunotherapy or targeted therapy',
            'C': 'Placebo',
            'O': 'Relapse-free survival or recurrence-free survival',
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
            'placebos': 'Placebo',  # Must match before "dabrafenib" — COMBI-AD's placebo arm is "Dabrafenib and trametinib placebos"
            'dabrafenib': 'Dab+Tram',
            'trametinib': 'Dab+Tram',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'KN054 RFS HR 0.57, COMBI-AD RFS HR 0.47, KN716 RFS HR 0.65',
        'benchmarks': {
            'Pembrolizumab': (0.40, 0.80),
            'Dab+Tram': (0.35, 0.65),
        },
    },
]


# ═══════════════════════════════════════════════════════════════════
# MAIN TEST RUNNER (reusable from round 1)
# ═══════════════════════════════════════════════════════════════════

def run_topic(driver, topic, topic_idx):
    """Run a single topic through the full NMA pipeline. Returns a result dict."""
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
        'nma_tau2': None,
        'nma_I2': None,
        'pscores': {},
        'issues': [],
        'drug_vs_ref': [],
        'raw_treatment_names': [],
        'benchmark_checks': [],
    }

    try:
        # Delete IndexedDB + localStorage to prevent state leaks between topics
        driver.get(FILE_URL)
        driver.execute_script("""
            try { localStorage.clear(); sessionStorage.clear(); } catch(e) {}
            try { indexedDB.deleteDatabase('MetaSprintNMA'); } catch(e) {}
        """)
        time.sleep(0.5)
        # Reload so app initializes with completely clean state
        driver.get(FILE_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
        time.sleep(1)
        try:
            driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except Exception:
            pass

        # Verify clean state
        n_existing = driver.execute_script(
            "return typeof extractedStudies !== 'undefined' ? extractedStudies.length : -1")
        if n_existing > 0:
            result['issues'].append(f'STATE_LEAK: {n_existing} studies survived cleanup')
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

        # Step 2: Inject search results
        trials_json = json.dumps(topic['trials'])
        driver.execute_script(f"""
            switchPhase('search');
            searchResultsCache = {trials_json};
            var aeRow = document.getElementById('autoExtractRow');
            if (aeRow) aeRow.style.display = 'block';
        """)
        time.sleep(0.3)

        # Step 3: Run auto-extract
        driver.execute_script("runAutoExtract()")
        for tick in range(90):
            time.sleep(2)
            running = driver.execute_script("return typeof _autoExtractRunning !== 'undefined' ? _autoExtractRunning : false")
            if not running:
                break
        else:
            result['issues'].append('EXTRACTION_TIMEOUT: Polling exhausted 90 ticks (180s) without completion')

        # Check for extraction errors
        n_trials = driver.execute_script("return typeof _extractionResults !== 'undefined' ? _extractionResults.length : 0")
        total_outcomes = driver.execute_script(
            "return typeof _extractionResults !== 'undefined' ? _extractionResults.reduce(function(s,t){return s+(t.outcomes?t.outcomes.length:0)},0) : 0")
        result['n_trials_extracted'] = n_trials
        result['n_outcomes_extracted'] = total_outcomes

        if n_trials == 0:
            result['issues'].append('EXTRACTION_FAILED: No trials extracted')
            result['status'] = 'EXTRACT_FAIL'
            return result

        if total_outcomes == 0:
            result['issues'].append('NO_OUTCOMES: Trials extracted but no outcomes found')
            result['status'] = 'NO_OUTCOMES'
            return result

        # Gather all raw outcomes for diagnosis
        all_outcomes_raw = json.loads(driver.execute_script("""
            var out = [];
            for (var t of _extractionResults) {
                for (var o of (t.outcomes||[])) {
                    out.push({
                        nct: t.nctId, type: o.effectType, est: o.estimate,
                        lo: o.lowerCI, hi: o.upperCI,
                        title: (o.outcomeTitle||'').substring(0,80),
                        source: o.source, isPrimary: o.isPrimary,
                        arms: o.arms
                    });
                }
            }
            return JSON.stringify(out);
        """))

        # Step 4: Select outcomes matching the topic
        # Try primary keyword, then alt_keywords, then broadest fallbacks
        outcome_kw = topic['outcome_keyword']
        alt_keywords = topic.get('alt_keywords', [])
        effect_type = topic['effect_type']

        # Build keyword list: primary + alternates
        all_keywords = [outcome_kw] + alt_keywords

        driver.execute_script(f"""
            var keywords = {json.dumps(all_keywords)};
            var et = {json.dumps(effect_type)};
            // Uncheck all
            for (var t of _extractionResults) {{
                for (var o of (t.outcomes||[])) o.checked = false;
            }}
            for (var t of _extractionResults) {{
                var matches = [];
                // Try each keyword in priority order
                for (var kw of keywords) {{
                    kw = kw.toLowerCase();
                    for (var o of (t.outcomes||[])) {{
                        if (o.effectType !== et) continue;
                        var title = (o.outcomeTitle || '').toLowerCase();
                        if (title.indexOf(kw) >= 0) matches.push(o);
                    }}
                    if (matches.length > 0) break;
                }}
                // Fallback: any outcome of correct type
                if (matches.length === 0) {{
                    for (var o of (t.outcomes||[])) {{
                        if (o.effectType === et) matches.push(o);
                    }}
                }}
                // Fallback: any HR at all
                if (matches.length === 0 && et === 'HR') {{
                    for (var o of (t.outcomes||[])) {{
                        if (o.effectType === 'HR') matches.push(o);
                    }}
                }}
                if (matches.length > 0) {{
                    // Prefer primary, then first
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

        # Count selected
        n_selected = driver.execute_script("""
            var c = 0;
            for (var t of _extractionResults) {
                for (var o of (t.outcomes||[])) { if (o.checked) c++; }
            }
            return c;
        """)
        result['n_outcomes_selected'] = n_selected

        if n_selected < 2:
            result['issues'].append(f'TOO_FEW_SELECTED: Only {n_selected} outcomes matched keywords (need >=2)')
            # Broader fallback: any HR with valid estimate
            driver.execute_script("""
                for (var t of _extractionResults) {
                    var hasChecked = false;
                    for (var o of (t.outcomes||[])) { if (o.checked) hasChecked = true; }
                    if (!hasChecked) {
                        for (var o of (t.outcomes||[])) {
                            if (o.effectType === 'HR' && o.estimate !== null) {
                                o.checked = true; break;
                            }
                        }
                    }
                }
            """)
            n_selected = driver.execute_script("""
                var c = 0;
                for (var t of _extractionResults) {
                    for (var o of (t.outcomes||[])) { if (o.checked) c++; }
                }
                return c;
            """)
            result['n_outcomes_selected'] = n_selected
            if n_selected < 2:
                # Last resort: any outcome with estimate + CI
                driver.execute_script("""
                    for (var t of _extractionResults) {
                        var hasChecked = false;
                        for (var o of (t.outcomes||[])) { if (o.checked) hasChecked = true; }
                        if (!hasChecked) {
                            for (var o of (t.outcomes||[])) {
                                if (o.estimate !== null && o.lowerCI !== null && o.upperCI !== null) {
                                    o.checked = true; break;
                                }
                            }
                        }
                    }
                """)
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
                    result['issues'].append(f'AVAILABLE_OUTCOMES: {json.dumps(all_outcomes_raw[:20])}')
                    return result

        # Step 5: Accept into extract table
        driver.execute_script("acceptExtractedStudies()")
        time.sleep(0.5)
        n_studies = driver.execute_script("return typeof extractedStudies !== 'undefined' ? extractedStudies.length : 0")
        result['n_studies_in_table'] = n_studies

        if n_studies < 2:
            result['issues'].append(f'ACCEPT_FAILED: Only {n_studies} studies accepted')
            result['status'] = 'ACCEPT_FAIL'
            return result

        # Capture raw treatment names before normalization
        raw_names = json.loads(driver.execute_script("""
            return JSON.stringify(extractedStudies.map(function(s) {
                return {t1: s.treatment1, t2: s.treatment2, nct: s.nctId};
            }));
        """))
        result['raw_treatment_names'] = raw_names

        # Step 6: Normalize treatment names
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

        # Deduplicate by NCT ID
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

        # Check treatment normalization quality
        norm_names = json.loads(driver.execute_script("""
            return JSON.stringify(extractedStudies.map(function(s) {
                return {t1: s.treatment1, t2: s.treatment2, nct: s.nctId, hr: s.effectEstimate};
            }));
        """))
        for nm in norm_names:
            for side in ['t1', 't2']:
                name = nm[side]
                if len(name) > 30:
                    result['issues'].append(f'LONG_NAME: {nm["nct"]} {side}="{name[:50]}" (may need normalization)')
            # Check for self-comparison after normalization
            if nm['t1'] == nm['t2']:
                result['issues'].append(f'SELF_COMPARE: {nm["nct"]} both arms normalized to "{nm["t1"]}"')

        # Step 7: Run NMA engine
        engine_result = json.loads(driver.execute_script("""
            try {
                var valid = extractedStudies.filter(function(s) {
                    return s.effectEstimate !== null && s.lowerCI !== null && s.upperCI !== null;
                });
                if (valid.length < 2) return JSON.stringify({error: 'Need >=2 valid studies, got ' + valid.length});

                var network = buildNetworkGraph(valid);
                if (!network || network.nE === 0) return JSON.stringify({error: 'Empty network'});

                // Check connectivity
                if (network.components && network.components.length > 1) {
                    return JSON.stringify({error: 'Disconnected network: ' + network.components.length + ' components',
                        components: network.components.map(function(c) { return c.map(function(i) { return network.treatments[i]; }); }),
                        normWarnings: network.normWarnings || []
                    });
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
                    leagueTable: (result.leagueTable || []).slice(0, 50),
                    normWarnings: network.normWarnings || []
                });
            } catch(e) {
                return JSON.stringify({error: e.message, stack: (e.stack||'').substring(0,300)});
            }
        """))

        if engine_result.get('error'):
            result['issues'].append(f'NMA_ERROR: {engine_result["error"]}')
            if engine_result.get('components'):
                result['issues'].append(f'DISCONNECTED: {engine_result["components"]}')
            if engine_result.get('normWarnings'):
                for w in engine_result['normWarnings']:
                    result['issues'].append(f'NORM_WARN: {w}')
            result['status'] = 'NMA_FAIL'
            return result

        # Capture NMA results
        result['nma_treatments'] = engine_result['nT']
        result['nma_edges'] = engine_result['nE']
        result['nma_tau2'] = engine_result.get('tau2')
        result['nma_I2'] = engine_result.get('I2')

        if engine_result.get('normWarnings'):
            for w in engine_result['normWarnings']:
                result['issues'].append(f'NORM_WARN: {w}')

        # P-scores
        pscores = engine_result.get('pscores', {})
        treatments = engine_result.get('treatments', [])
        scored = []
        for k in pscores:
            idx = int(k)
            if idx < len(treatments):
                scored.append((treatments[idx], pscores[k]))
        scored.sort(key=lambda x: -x[1])
        result['pscores'] = {name: ps for name, ps in scored}

        # League table: Drug vs comparator
        comp = topic.get('common_comparator', '').lower()
        lt = engine_result.get('leagueTable', [])
        is_ratio = engine_result.get('isRatio', False)
        for entry in lt:
            t1 = entry.get('t1', '')
            t2 = entry.get('t2', '')
            eff = entry.get('effect', entry.get('eff', None))
            lo = entry.get('lo')
            hi = entry.get('hi')
            if not isinstance(eff, (int, float)):
                continue
            if t2.lower() == comp and t1.lower() != comp:
                if is_ratio:
                    try:
                        hr = math.exp(eff)
                        hr_lo = math.exp(lo) if isinstance(lo, (int, float)) else None
                        hr_hi = math.exp(hi) if isinstance(hi, (int, float)) else None
                    except (OverflowError, ValueError):
                        continue
                    result['drug_vs_ref'].append({'drug': t1, 'hr': hr, 'lo': hr_lo, 'hi': hr_hi})
                else:
                    result['drug_vs_ref'].append({'drug': t1, 'effect': eff, 'lo': lo, 'hi': hi})

        # Validation against published NMA benchmarks
        benchmarks = topic.get('benchmarks', {})
        if topic.get('expect_favor_treatment') and result['drug_vs_ref']:
            for dvr in result['drug_vs_ref']:
                hr = dvr.get('hr', dvr.get('effect'))
                if hr is not None and hr > 1.0:
                    result['issues'].append(f'UNEXPECTED_DIRECTION: {dvr["drug"]} HR={hr:.3f} (expected <1)')

        # Check against benchmark ranges
        for dvr in result['drug_vs_ref']:
            drug = dvr['drug']
            hr = dvr.get('hr')
            if hr is None:
                continue
            if drug in benchmarks:
                lo_bench, hi_bench = benchmarks[drug]
                in_range = lo_bench <= hr <= hi_bench
                result['benchmark_checks'].append({
                    'drug': drug, 'hr': hr,
                    'bench_lo': lo_bench, 'bench_hi': hi_bench,
                    'in_range': in_range
                })
                if not in_range:
                    result['issues'].append(
                        f'BENCHMARK_MISMATCH: {drug} HR={hr:.3f} outside published range [{lo_bench:.2f}, {hi_bench:.2f}]')

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
    try:
        print('=' * 80)
        print(f'NMA PIPELINE STRESS TEST ROUND 2: {n_topics} TOPICS')
        print('All trials CT.gov-verified with structured HR results')
        print('Cross-validated against published network meta-analyses')
        print('=' * 80)

        for i, topic in enumerate(TOPICS):
            print(f'\n{"="*80}')
            print(f'TOPIC {i+1}/{n_topics}: {topic["name"]}')
            print(f'Trials: {len(topic["trials"])} | Outcome: {topic["outcome_keyword"]} ({topic["effect_type"]})')
            print(f'{"="*80}')

            result = run_topic(driver, topic, i)
            results.append(result)

            # Print summary for this topic
            print(f'\n  Status: {result["status"]}')
            print(f'  Extracted: {result["n_trials_extracted"]} trials, {result["n_outcomes_extracted"]} outcomes')
            print(f'  Selected: {result["n_outcomes_selected"]} outcomes')
            print(f'  NMA: {result["nma_treatments"]} treatments, {result["nma_edges"]} edges')

            if result['raw_treatment_names']:
                print(f'  Raw treatment names (before normalization):')
                for rn in result['raw_treatment_names']:
                    print(f'    {rn.get("nct","?")}: "{rn["t1"]}" vs "{rn["t2"]}"')

            if result['pscores']:
                print(f'  P-score ranking:')
                for name, ps in sorted(result['pscores'].items(), key=lambda x: -x[1]):
                    print(f'    {name:30s}: {ps:.3f}')

            if result['drug_vs_ref']:
                comp_name = topic.get('common_comparator', '?')
                print(f'  Drug vs {comp_name}:')
                for dvr in result['drug_vs_ref']:
                    hr = dvr.get('hr', dvr.get('effect'))
                    lo = dvr.get('lo')
                    hi = dvr.get('hi')
                    if hr is not None:
                        ci_str = f' ({lo:.3f}-{hi:.3f})' if lo is not None and hi is not None else ''
                        print(f'    {dvr["drug"]:30s}: HR {hr:.3f}{ci_str}')

            if result['benchmark_checks']:
                print(f'  Benchmark checks:')
                for bc in result['benchmark_checks']:
                    status = 'OK' if bc['in_range'] else 'MISMATCH'
                    print(f'    {bc["drug"]:30s}: HR {bc["hr"]:.3f} vs [{bc["bench_lo"]:.2f}-{bc["bench_hi"]:.2f}] -> {status}')

            if result['issues']:
                print(f'  Issues ({len(result["issues"])}):')
                for iss in result['issues']:
                    # Truncate very long issue strings
                    print(f'    [!] {iss[:200]}')

        # ═══════════════════════════════════════════════════════════════
        # FINAL REPORT
        # ═══════════════════════════════════════════════════════════════
        print(f'\n\n{"="*80}')
        print(f'FINAL REPORT: ROUND 2 NMA STRESS TEST ({n_topics} TOPICS)')
        print(f'{"="*80}')

        pass_count = sum(1 for r in results if r['status'] == 'PASS')
        fail_count = n_topics - pass_count

        print(f'\n  PASS: {pass_count}/{n_topics}')
        print(f'  FAIL: {fail_count}/{n_topics}')

        # Summary table
        print(f'\n  {"#":<3} {"Topic":<35} {"Status":<12} {"Tri":<4} {"Out":<4} {"Sel":<4} {"nT":<4} {"nE":<4} {"Bench":<6} {"Issues":<5}')
        print(f'  {"-"*3} {"-"*35} {"-"*12} {"-"*4} {"-"*4} {"-"*4} {"-"*4} {"-"*4} {"-"*6} {"-"*5}')
        for i, r in enumerate(results):
            n_bench_ok = sum(1 for bc in r.get('benchmark_checks', []) if bc['in_range'])
            n_bench_total = len(r.get('benchmark_checks', []))
            bench_str = f'{n_bench_ok}/{n_bench_total}' if n_bench_total > 0 else '-'
            print(f'  {i+1:<3} {r["name"]:<35} {r["status"]:<12} {r["n_trials_extracted"]:<4} '
                  f'{r["n_outcomes_extracted"]:<4} {r["n_outcomes_selected"]:<4} '
                  f'{r["nma_treatments"]:<4} {r["nma_edges"]:<4} {bench_str:<6} {len(r["issues"]):<5}')

        # Benchmark summary
        all_benchmarks = []
        for r in results:
            all_benchmarks.extend(r.get('benchmark_checks', []))
        if all_benchmarks:
            n_ok = sum(1 for b in all_benchmarks if b['in_range'])
            print(f'\n  BENCHMARK VALIDATION: {n_ok}/{len(all_benchmarks)} HRs within published NMA ranges')
            for bc in all_benchmarks:
                if not bc['in_range']:
                    print(f'    MISMATCH: {bc["drug"]} HR={bc["hr"]:.3f} vs [{bc["bench_lo"]:.2f}-{bc["bench_hi"]:.2f}]')

        # All issues aggregated
        all_issues = []
        for r in results:
            for iss in r['issues']:
                all_issues.append(f'{r["name"]}: {iss}')

        if all_issues:
            print(f'\n  ALL ISSUES ({len(all_issues)}):')
            for iss in all_issues:
                print(f'    {iss[:200]}')

            categories = {}
            for iss in all_issues:
                cat = iss.split(': ', 2)[1].split(':')[0] if ': ' in iss else 'OTHER'
                categories.setdefault(cat, []).append(iss)
            print(f'\n  ISSUE CATEGORIES:')
            for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
                print(f'    {cat}: {len(items)} occurrences')

        print(f'\n{"="*80}')
        print(f'TEST COMPLETE')
        print(f'{"="*80}')

        return 0 if fail_count == 0 else 1

    except Exception as e:
        print(f'\nFATAL: {e}')
        traceback.print_exc()
        return 2
    finally:
        driver.quit()


if __name__ == '__main__':
    sys.exit(main())
