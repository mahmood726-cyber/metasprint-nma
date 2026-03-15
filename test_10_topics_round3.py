"""
NMA Pipeline Stress Test Round 3: 10 New Topics with CT.gov-Verified HRs
=========================================================================
All trials have CONFIRMED structured HR results on ClinicalTrials.gov.
Each topic cross-referenced against published NMAs for HR validation.
Focus: post-2015 RCTs, diverse disease areas, all data points user-verifiable.

Topics: nephrology, urology-oncology, gynecologic oncology, cardiology, hepatology
"""
import io, sys, os, time, json, math, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metasprint-nma.html')
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')

# ═══════════════════════════════════════════════════════════════════
# TOPIC CONFIGURATIONS — 10 new topics, all CT.gov HR-verified
# ═══════════════════════════════════════════════════════════════════

TOPICS = [
    # ── Topic 1: CKD Nephroprotection — Kidney Composite (HR) ──
    # Published NMA: Defined Daily Dose comparison NMAs; Lancet 2022 meta
    # CREDENCE, DAPA-CKD, EMPA-KIDNEY, FIDELIO — all with kidney composite HR
    {
        'name': 'CKD Nephroprotection',
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
        'benchmark_note': 'CREDENCE HR 0.70, DAPA-CKD HR 0.61, EMPA-KIDNEY HR 0.72, FIDELIO HR 0.82',
        'benchmarks': {
            'Canagliflozin': (0.55, 0.85),
            'Dapagliflozin': (0.45, 0.75),
            'Empagliflozin': (0.55, 0.90),
            'Finerenone': (0.65, 0.95),
        },
    },

    # ── Topic 2: DKD Cardiovascular Outcomes — CV Composite (HR) ──
    # FIGARO-DKD and FIDELIO-DKD: finerenone CV outcomes in DKD
    # CREDENCE, DAPA-CKD also have CV secondary endpoints
    {
        'name': 'DKD CV Outcomes',
        'pico': {
            'P': 'Adults with type 2 diabetes and chronic kidney disease',
            'I': 'SGLT2 inhibitor or MRA',
            'C': 'Placebo',
            'O': 'Cardiovascular death or hospitalization',
        },
        'trials': [
            {'nctId': 'NCT02545049', 'pmid': '34449181', 'title': 'FIGARO-DKD (Finerenone CV in DKD)',
             'authors': 'Pitt B', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT02540993', 'pmid': '33264825', 'title': 'FIDELIO-DKD (Finerenone renal in DKD)',
             'authors': 'Bakris GL', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT02065791', 'pmid': '30990260', 'title': 'CREDENCE (Canagliflozin DKD)',
             'authors': 'Perkovic V', 'year': '2019', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'cardiovascular',
        'alt_keywords': ['cv death', 'cardiac', 'mace', 'heart failure'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'finerenone': 'Finerenone',
            'canagliflozin': 'Canagliflozin',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'FIGARO CV HR 0.87, FIDELIO CV HR 0.86, CREDENCE CV HR ~0.80',
        'benchmarks': {
            'Finerenone': (0.70, 1.00),   # pooled from FIGARO+FIDELIO
            'Canagliflozin': (0.65, 0.95),
        },
    },

    # ── Topic 3: 1L Urothelial Carcinoma ICI+Chemo vs Chemo (OS) ──
    # Published NMA: Lancet Oncol 2023, multiple NMAs
    # JAVELIN Bladder 100 = maintenance, KEYNOTE-361 = 1L combo, IMvigor130 = 1L combo
    {
        'name': '1L Urothelial ICI OS',
        'pico': {
            'P': 'Advanced or metastatic urothelial carcinoma, first-line',
            'I': 'Immune checkpoint inhibitor with or after chemotherapy',
            'C': 'Chemotherapy or best supportive care',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT02603432', 'pmid': '32945632', 'title': 'JAVELIN Bladder 100 (Avelumab maintenance)',
             'authors': 'Powles T', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT02853305', 'pmid': '34051178', 'title': 'KEYNOTE-361 (Pembro+Chemo 1L UC)',
             'authors': 'Powles T', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT02807636', 'pmid': '32416780', 'title': 'IMvigor130 (Atezo+Chemo 1L UC)',
             'authors': 'Galsky MD', 'year': '2020', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'alt_keywords': ['survival', 'death', 'os'],
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            # JAVELIN: maintenance avelumab vs BSC (after chemo)
            'avelumab': 'Avel+BSC',
            'best supportive care': 'Chemo',
            'bsc': 'Chemo',
            # KEYNOTE-361: pembro+chemo vs chemo
            'pembrolizumab': 'Pembro+Chemo',
            # IMvigor130: atezo+chemo vs placebo+chemo
            'atezolizumab': 'Atezo+Chemo',
            # Comparator fallbacks
            'chemotherapy': 'Chemo',
            'placebo': 'Chemo',
            'gemcitabine': 'Chemo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'JAVELIN OS HR 0.69, KN-361 OS HR 0.86 (NS), IMvigor130 OS HR 0.85',
        'benchmarks': {
            'Avel+BSC': (0.50, 0.85),
            'Pembro+Chemo': (0.65, 1.05),   # did not meet OS significance
            'Atezo+Chemo': (0.65, 1.05),
        },
    },

    # ── Topic 4: 2L Urothelial Cancer ICI vs Chemo (OS) ──
    # KEYNOTE-045: pembro vs chemo in 2L UC
    # CheckMate 274: nivo adjuvant (different setting — skip)
    # Use single-trial topic to test pipeline with minimal data
    {
        'name': '2L Urothelial ICI vs Chemo',
        'pico': {
            'P': 'Recurrent or progressive metastatic urothelial carcinoma after platinum',
            'I': 'Pembrolizumab',
            'C': 'Investigator choice chemotherapy',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT02256436', 'pmid': '28212060', 'title': 'KEYNOTE-045 (Pembro vs Chemo 2L UC)',
             'authors': 'Bellmunt J', 'year': '2017', 'source': 'ctgov'},
            {'nctId': 'NCT02853305', 'pmid': '34051178', 'title': 'KEYNOTE-361 (Pembro mono vs Chemo 1L)',
             'authors': 'Powles T', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'alt_keywords': ['survival', 'death'],
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            'pembrolizumab': 'Pembrolizumab',
            'chemotherapy': 'Chemo',
            'paclitaxel': 'Chemo',
            'docetaxel': 'Chemo',
            'vinflunine': 'Chemo',
            'placebo': 'Chemo',
            'gemcitabine': 'Chemo',
            'control': 'Chemo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'KN-045 OS HR 0.73, KN-361 pembro mono HR 0.92 (NS)',
        'benchmarks': {
            'Pembrolizumab': (0.55, 1.05),  # KN-045 sig, KN-361 mono NS
        },
    },

    # ── Topic 5: Endometrial Cancer 2L (Lenvatinib+Pembro vs Chemo) ──
    # KEYNOTE-775 / Study 309: landmark trial
    {
        'name': 'Endometrial Cancer 2L',
        'pico': {
            'P': 'Advanced endometrial carcinoma after prior platinum therapy',
            'I': 'Lenvatinib plus pembrolizumab',
            'C': 'Chemotherapy (doxorubicin or paclitaxel)',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT03517449', 'pmid': '35045221', 'title': 'KEYNOTE-775 (Len+Pembro vs Chemo)',
             'authors': 'Makker V', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT03884101', 'pmid': '39591551', 'title': 'LEAP-001 (Len+Pembro vs Chemo 1L)',
             'authors': 'Marth C', 'year': '2024', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'alt_keywords': ['survival', 'death', 'os'],
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            'lenvatinib': 'Len+Pembro',
            'pembrolizumab': 'Len+Pembro',
            'doxorubicin': 'Chemo',
            'paclitaxel': 'Chemo',
            'carboplatin': 'Chemo',
            "physician's choice": 'Chemo',
            'treatment of': 'Chemo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'KN-775 OS HR 0.62, LEAP-001 OS HR ~1.0 (1L not superior)',
        'benchmarks': {
            'Len+Pembro': (0.45, 1.10),  # KN-775 positive, LEAP-001 negative
        },
    },

    # ── Topic 6: SGLT2i All-Cause Mortality in HF (HR) ──
    # DAPA-HF, EMPEROR-Reduced, EMPEROR-Preserved — mortality endpoint
    {
        'name': 'SGLT2i HF Mortality',
        'pico': {
            'P': 'Adults with heart failure (HFrEF or HFpEF)',
            'I': 'SGLT2 inhibitor',
            'C': 'Placebo',
            'O': 'All-cause mortality',
        },
        'trials': [
            {'nctId': 'NCT03036124', 'pmid': '31535829', 'title': 'DAPA-HF (Dapagliflozin HFrEF)',
             'authors': 'McMurray JJV', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT03057977', 'pmid': '32865377', 'title': 'EMPEROR-Reduced (Empagliflozin HFrEF)',
             'authors': 'Packer M', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT03057951', 'pmid': '34449189', 'title': 'EMPEROR-Preserved (Empagliflozin HFpEF)',
             'authors': 'Anker SD', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'mortality',
        'alt_keywords': ['death', 'all-cause', 'all cause'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'dapa': 'Dapagliflozin',
            'dapagliflozin': 'Dapagliflozin',
            'empagliflozin': 'Empagliflozin',
            '10 mg empagliflozin': 'Empagliflozin',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'DAPA-HF mortality HR 0.83, EMPEROR-Reduced HR 0.92, EMPEROR-Preserved HR 1.00',
        'benchmarks': {
            'Dapagliflozin': (0.65, 1.00),
            'Empagliflozin': (0.70, 1.10),  # includes HFpEF where mortality NS
        },
    },

    # ── Topic 7: GLP-1 RA Renal Outcomes (HR) ──
    # LEADER, SUSTAIN-6, HARMONY renal composite
    {
        'name': 'GLP-1 RA Renal Outcomes',
        'pico': {
            'P': 'Adults with type 2 diabetes at high cardiovascular risk',
            'I': 'GLP-1 receptor agonist',
            'C': 'Placebo',
            'O': 'Renal composite outcome',
        },
        'trials': [
            {'nctId': 'NCT01179048', 'pmid': '27295427', 'title': 'LEADER (Liraglutide renal)',
             'authors': 'Marso SP', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT01720446', 'pmid': '27633186', 'title': 'SUSTAIN-6 (Semaglutide renal)',
             'authors': 'Marso SP', 'year': '2016', 'source': 'ctgov'},
            {'nctId': 'NCT02465515', 'pmid': '30291013', 'title': 'Harmony Outcomes (Albiglutide renal)',
             'authors': 'Hernandez AF', 'year': '2018', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'renal',
        'alt_keywords': ['nephropathy', 'kidney', 'creatinine', 'macroalbuminuria'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'liraglutide': 'Liraglutide',
            'semaglutide': 'Semaglutide',
            'albiglutide': 'Albiglutide',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'LEADER renal HR 0.78, SUSTAIN-6 renal HR 0.64, HARMONY renal ~0.90',
        'benchmarks': {
            'Liraglutide': (0.60, 0.95),
            'Semaglutide': (0.45, 0.85),
        },
    },

    # ── Topic 8: 1L HCC Atezo+Bev vs Sorafenib PFS (HR) ──
    # IMbrave150, HIMALAYA, CheckMate 459 — PFS instead of OS
    {
        'name': '1L HCC PFS',
        'pico': {
            'P': 'Unresectable hepatocellular carcinoma, first-line',
            'I': 'Immune checkpoint inhibitor combination',
            'C': 'Sorafenib',
            'O': 'Progression-free survival',
        },
        'trials': [
            {'nctId': 'NCT03434379', 'pmid': '32402160', 'title': 'IMbrave150 (Atezo+Bev PFS)',
             'authors': 'Finn RS', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT03298451', 'pmid': '38319892', 'title': 'HIMALAYA (Durva+Treme PFS)',
             'authors': 'Abou-Alfa GK', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT02576509', 'pmid': '34914889', 'title': 'CheckMate 459 (Nivo PFS)',
             'authors': 'Yau T', 'year': '2022', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'progression',
        'alt_keywords': ['pfs', 'progression-free', 'disease-free'],
        'effect_type': 'HR',
        'common_comparator': 'Sorafenib',
        'norm_map': {
            # HIMALAYA om.groups use dosage labels
            'treme': 'Durva+Treme',
            'sora': 'Sorafenib',
            # IMbrave150
            'atezolizumab': 'Atezo+Bev',
            'bevacizumab': 'Atezo+Bev',
            # CheckMate 459
            'nivolumab': 'Nivolumab',
            # Comparator
            'sorafenib': 'Sorafenib',
            # HIMALAYA drug names
            'durvalumab': 'Durva+Treme',
            'tremelimumab': 'Durva+Treme',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'IMbrave150 PFS HR 0.59, HIMALAYA PFS ~0.90, CM459 PFS HR 0.93',
        'benchmarks': {
            'Atezo+Bev': (0.40, 0.75),
            'Durva+Treme': (0.65, 1.10),   # PFS was not significant for HIMALAYA
            'Nivolumab': (0.70, 1.10),
        },
    },

    # ── Topic 9: Finerenone CV vs Renal (dual-endpoint comparison) ──
    # Both FIDELIO and FIGARO have renal AND CV composites
    {
        'name': 'Finerenone Dual Endpoints',
        'pico': {
            'P': 'Adults with type 2 diabetes and diabetic kidney disease',
            'I': 'Finerenone',
            'C': 'Placebo',
            'O': 'All-cause mortality',
        },
        'trials': [
            {'nctId': 'NCT02540993', 'pmid': '33264825', 'title': 'FIDELIO-DKD (Finerenone)',
             'authors': 'Bakris GL', 'year': '2020', 'source': 'ctgov'},
            {'nctId': 'NCT02545049', 'pmid': '34449181', 'title': 'FIGARO-DKD (Finerenone)',
             'authors': 'Pitt B', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'mortality',
        'alt_keywords': ['death', 'all-cause', 'all cause'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'finerenone': 'Finerenone',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'FIDELIO mortality HR 0.90, FIGARO mortality HR 0.89',
        'benchmarks': {
            'Finerenone': (0.70, 1.10),  # neither reached significance for mortality alone
        },
    },

    # ── Topic 10: PARP Inhibitor 1L Ovarian Maintenance (PFS HR) ──
    # PRIMA (niraparib), PAOLA-1 (olaparib+bev), VELIA (veliparib) — 1L maintenance
    {
        'name': '1L Ovarian PARP Maintenance',
        'pico': {
            'P': 'Newly diagnosed advanced ovarian cancer after first-line platinum response',
            'I': 'PARP inhibitor maintenance',
            'C': 'Placebo',
            'O': 'Progression-free survival',
        },
        'trials': [
            {'nctId': 'NCT02655016', 'pmid': '31562799', 'title': 'PRIMA (Niraparib 1L maintenance)',
             'authors': 'Gonzalez-Martin A', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02477644', 'pmid': '31851799', 'title': 'PAOLA-1 (Olaparib+Bev 1L maintenance)',
             'authors': 'Ray-Coquard I', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02470585', 'pmid': '31562800', 'title': 'VELIA (Veliparib 1L maintenance)',
             'authors': 'Coleman RL', 'year': '2019', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'progression',
        'alt_keywords': ['pfs', 'disease progression', 'recurrence'],
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'niraparib': 'Niraparib',
            'olaparib': 'Olaparib+Bev',
            'veliparib': 'Veliparib',
            'placebo': 'Placebo',
            'bevacizumab': 'Olaparib+Bev',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'PRIMA PFS HR 0.62, PAOLA-1 PFS HR 0.59, VELIA PFS HR 0.68',
        'benchmarks': {
            'Niraparib': (0.40, 0.80),
            'Olaparib+Bev': (0.40, 0.80),
            'Veliparib': (0.35, 0.90),
        },
    },
]


# ═══════════════════════════════════════════════════════════════════
# MAIN TEST RUNNER (shared with round 1/2)
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

        all_outcomes_raw = json.loads(driver.execute_script("""
            var out = [];
            for (var t of _extractionResults) {
                for (var o of (t.outcomes||[])) {
                    out.push({
                        nct: t.nctId, type: o.effectType, est: o.estimate,
                        lo: o.lowerCI, hi: o.upperCI,
                        title: (o.outcomeTitle||'').substring(0,80),
                        source: o.source, isPrimary: o.isPrimary,
                        arms: o.arms,
                        fieldPath: o.evidence && o.evidence.ctgov ? o.evidence.ctgov.fieldPath : null
                    });
                }
            }
            return JSON.stringify(out);
        """))

        # Check provenance: every outcome should have a fieldPath
        n_with_provenance = sum(1 for o in all_outcomes_raw if o.get('fieldPath'))
        if n_with_provenance < len(all_outcomes_raw):
            n_missing = len(all_outcomes_raw) - n_with_provenance
            result['issues'].append(f'PROVENANCE_GAP: {n_missing}/{len(all_outcomes_raw)} outcomes missing fieldPath')

        # Step 4: Select outcomes matching the topic
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
                if (matches.length === 0 && et === 'HR') {{
                    for (var o of (t.outcomes||[])) {{
                        if (o.effectType === 'HR') matches.push(o);
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
            result['issues'].append(f'TOO_FEW_SELECTED: Only {n_selected} outcomes matched keywords')
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

        result['nma_treatments'] = engine_result['nT']
        result['nma_edges'] = engine_result['nE']
        result['nma_tau2'] = engine_result.get('tau2')
        result['nma_I2'] = engine_result.get('I2')

        if engine_result.get('normWarnings'):
            for w in engine_result['normWarnings']:
                result['issues'].append(f'NORM_WARN: {w}')

        pscores = engine_result.get('pscores', {})
        treatments = engine_result.get('treatments', [])
        scored = []
        for k in pscores:
            idx = int(k)
            if idx < len(treatments):
                scored.append((treatments[idx], pscores[k]))
        scored.sort(key=lambda x: -x[1])
        result['pscores'] = {name: ps for name, ps in scored}

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

        benchmarks = topic.get('benchmarks', {})
        if topic.get('expect_favor_treatment') and result['drug_vs_ref']:
            for dvr in result['drug_vs_ref']:
                hr = dvr.get('hr', dvr.get('effect'))
                if hr is not None and hr > 1.0:
                    result['issues'].append(f'UNEXPECTED_DIRECTION: {dvr["drug"]} HR={hr:.3f} (expected <1)')

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
        print(f'NMA PIPELINE STRESS TEST ROUND 3: {n_topics} TOPICS')
        print('All trials CT.gov-verified with structured HR results')
        print('Focus: nephrology, urology-onc, gyn-onc, cardiology, hepatology')
        print('=' * 80)

        for i, topic in enumerate(TOPICS):
            print(f'\n{"="*80}')
            print(f'TOPIC {i+1}/{n_topics}: {topic["name"]}')
            print(f'Trials: {len(topic["trials"])} | Outcome: {topic["outcome_keyword"]} ({topic["effect_type"]})')
            print(f'{"="*80}')

            result = run_topic(driver, topic, i)
            results.append(result)

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
                    print(f'    [!] {iss[:200]}')

        # FINAL REPORT
        print(f'\n\n{"="*80}')
        print(f'FINAL REPORT: ROUND 3 NMA STRESS TEST ({n_topics} TOPICS)')
        print(f'{"="*80}')

        pass_count = sum(1 for r in results if r['status'] == 'PASS')
        fail_count = n_topics - pass_count

        print(f'\n  PASS: {pass_count}/{n_topics}')
        print(f'  FAIL: {fail_count}/{n_topics}')

        print(f'\n  {"#":<3} {"Topic":<35} {"Status":<12} {"Tri":<4} {"Out":<4} {"Sel":<4} {"nT":<4} {"nE":<4} {"Bench":<6} {"Issues":<5}')
        print(f'  {"-"*3} {"-"*35} {"-"*12} {"-"*4} {"-"*4} {"-"*4} {"-"*4} {"-"*4} {"-"*6} {"-"*5}')
        for i, r in enumerate(results):
            n_bench_ok = sum(1 for bc in r.get('benchmark_checks', []) if bc['in_range'])
            n_bench_total = len(r.get('benchmark_checks', []))
            bench_str = f'{n_bench_ok}/{n_bench_total}' if n_bench_total > 0 else '-'
            print(f'  {i+1:<3} {r["name"]:<35} {r["status"]:<12} {r["n_trials_extracted"]:<4} '
                  f'{r["n_outcomes_extracted"]:<4} {r["n_outcomes_selected"]:<4} '
                  f'{r["nma_treatments"]:<4} {r["nma_edges"]:<4} {bench_str:<6} {len(r["issues"]):<5}')

        all_benchmarks = []
        for r in results:
            all_benchmarks.extend(r.get('benchmark_checks', []))
        if all_benchmarks:
            n_ok = sum(1 for b in all_benchmarks if b['in_range'])
            print(f'\n  BENCHMARK VALIDATION: {n_ok}/{len(all_benchmarks)} HRs within published NMA ranges')
            for bc in all_benchmarks:
                if not bc['in_range']:
                    print(f'    MISMATCH: {bc["drug"]} HR={bc["hr"]:.3f} vs [{bc["bench_lo"]:.2f}-{bc["bench_hi"]:.2f}]')

        all_issues = []
        for r in results:
            for iss in r['issues']:
                all_issues.append(f'{r["name"]}: {iss}')
        if all_issues:
            print(f'\n  ALL ISSUES ({len(all_issues)}):')
            for iss in all_issues:
                print(f'    {iss[:200]}')

    finally:
        driver.quit()

    print(f'\n{"="*80}')
    print(f'TEST COMPLETE')
    print(f'{"="*80}')
    sys.exit(0 if pass_count == n_topics else 1)


if __name__ == '__main__':
    main()
