"""
Comprehensive NMA Pipeline Stress Test: 10 Disease Topics
===========================================================
Tests the full pipeline: CT.gov search → extract → select → NMA engine
for 10 diverse oncology/cardiology topics.

Each topic uses a star network (multiple treatments vs common comparator).
Identifies issues in: search, extraction, treatment normalization, NMA engine.
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
# TOPIC CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════

TOPICS = [
    # ── Topic 1: mHSPC (metastatic hormone-sensitive prostate cancer) ──
    {
        'name': 'mHSPC First-Line Intensification',
        'pico': {
            'P': 'Metastatic hormone-sensitive prostate cancer',
            'I': 'Novel hormonal agents + ADT',
            'C': 'ADT alone or ADT + docetaxel',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT02677896', 'pmid': '31329516', 'title': 'ARCHES (Enzalutamide+ADT)',
             'authors': 'Armstrong AJ', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02489318', 'pmid': '31150574', 'title': 'TITAN (Apalutamide+ADT)',
             'authors': 'Chi KN', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02799602', 'pmid': '35179323', 'title': 'ARASENS (Darolutamide+Docetaxel+ADT)',
             'authors': 'Smith MR', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT04736199', 'pmid': '', 'title': 'ARANOTE (Darolutamide+ADT)',
             'authors': 'Tombal B', 'year': '2024', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'effect_type': 'HR',
        'common_comparator': 'ADT',
        'norm_map': {
            'enzalutamide': 'Enzalutamide+ADT',
            'apalutamide': 'Apalutamide+ADT',
            'darolutamide': 'Darolutamide+ADT',
            'placebo': 'ADT',
            'adt': 'ADT',
            'androgen deprivation': 'ADT',
            'docetaxel': 'Docetaxel+ADT',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'All novel agents improve OS vs ADT alone',
    },
    # ── Topic 2: HCC First-Line (vs Sorafenib) ──
    {
        'name': 'HCC First-Line Systemic',
        'pico': {
            'P': 'Unresectable hepatocellular carcinoma',
            'I': 'ICI-based combos or lenvatinib',
            'C': 'Sorafenib',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT01761266', 'pmid': '29433850', 'title': 'REFLECT (Lenvatinib vs Sorafenib)',
             'authors': 'Kudo M', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT03755791', 'pmid': '35798016', 'title': 'COSMIC-312 (Cabo+Atezo vs Sorafenib)',
             'authors': 'Kelley RK', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT00105443', 'pmid': '18650514', 'title': 'SHARP (Sorafenib vs Placebo)',
             'authors': 'Llovet JM', 'year': '2008', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'effect_type': 'HR',
        'common_comparator': 'Sorafenib',
        'norm_map': {
            'sorafenib': 'Sorafenib',
            'lenvatinib': 'Lenvatinib',
            'cabozantinib': 'Cabo+Atezo',
            'atezolizumab': 'Cabo+Atezo',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': None,  # REFLECT is non-inferiority
        'benchmark_note': 'REFLECT: Lenvatinib non-inferior to Sorafenib (OS HR ~0.92)',
    },
    # ── Topic 3: EGFR NSCLC First-Line TKIs (vs Gefitinib) ──
    # FLAURA & ARCHER both use Gefitinib as comparator → connected star
    {
        'name': 'EGFR-Mutant NSCLC First-Line TKIs',
        'pico': {
            'P': 'EGFR-mutant advanced NSCLC',
            'I': 'Osimertinib or Dacomitinib',
            'C': 'Gefitinib',
            'O': 'Progression-free survival',
        },
        'trials': [
            {'nctId': 'NCT02296125', 'pmid': '29151359', 'title': 'FLAURA (Osimertinib vs Gefitinib/Erlotinib)',
             'authors': 'Soria JC', 'year': '2018', 'source': 'ctgov'},
            {'nctId': 'NCT01774721', 'pmid': '28958502', 'title': 'ARCHER 1050 (Dacomitinib vs Gefitinib)',
             'authors': 'Wu YL', 'year': '2017', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'progression',
        'effect_type': 'HR',
        'common_comparator': 'Gefitinib',
        'norm_map': {
            'osimertinib': 'Osimertinib',
            'azd9291': 'Osimertinib',
            'dacomitinib': 'Dacomitinib',
            'gefitinib': 'Gefitinib',
            'erlotinib': 'Gefitinib',  # FLAURA SoC = Gefitinib or Erlotinib — merge
            'standard of care': 'Gefitinib',
            'soc egfr': 'Gefitinib',   # CT.gov label "SoC EGFR-TKI"
            'egfr-tki': 'Gefitinib',   # catches "EGFR-TKI" suffix
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'Osimertinib > Dacomitinib > Gefitinib for PFS',
    },
    # ── Topic 4: Melanoma First-Line ──
    {
        'name': 'Advanced Melanoma First-Line',
        'pico': {
            'P': 'Unresectable/metastatic melanoma',
            'I': 'Pembrolizumab, Nivolumab+Ipilimumab',
            'C': 'Ipilimumab or Nivolumab alone',
            'O': 'Overall survival or PFS',
        },
        'trials': [
            {'nctId': 'NCT01866319', 'pmid': '25891173', 'title': 'KEYNOTE-006 (Pembro vs Ipi)',
             'authors': 'Robert C', 'year': '2015', 'source': 'ctgov'},
            {'nctId': 'NCT03470922', 'pmid': '34986285', 'title': 'RELATIVITY-047 (Relatlimab+Nivo vs Nivo)',
             'authors': 'Tawbi HA', 'year': '2022', 'source': 'ctgov'},
            {'nctId': 'NCT01515189', 'pmid': '28359784', 'title': 'Ipi 3mg vs 10mg',
             'authors': 'Ascierto PA', 'year': '2017', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'survival',
        'effect_type': 'HR',
        'common_comparator': 'Ipilimumab',
        'norm_map': {
            'pembrolizumab': 'Pembrolizumab',
            'nivolumab': 'Nivolumab',
            'ipilimumab': 'Ipilimumab',
            'relatlimab': 'Rela+Nivo',
            'mk-3475': 'Pembrolizumab',
        },
        'expect_favor_treatment': None,  # Mixed comparators (Ipi, Nivo) — direction varies
        'benchmark_note': 'KEYNOTE-006: Pembro > Ipi for OS',
    },
    # ── Topic 5: HFrEF SGLT2 Inhibitors ──
    {
        'name': 'HFrEF SGLT2 Inhibitors',
        'pico': {
            'P': 'Chronic heart failure with reduced ejection fraction',
            'I': 'SGLT2 inhibitors (dapagliflozin, empagliflozin)',
            'C': 'Placebo',
            'O': 'CV death or worsening HF',
        },
        'trials': [
            {'nctId': 'NCT03036124', 'pmid': '31535829', 'title': 'DAPA-HF (Dapagliflozin)',
             'authors': 'McMurray JJV', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT03057977', 'pmid': '32865377', 'title': 'EMPEROR-Reduced (Empagliflozin)',
             'authors': 'Packer M', 'year': '2020', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'death',
        'effect_type': 'HR',
        'common_comparator': 'Placebo',
        'norm_map': {
            'dapagliflozin': 'Dapagliflozin',
            'empagliflozin': 'Empagliflozin',
            'placebo': 'Placebo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'Both SGLT2i reduce CV death/HF hospitalization (HR ~0.74-0.75)',
    },
    # ── Topic 6: Multiple Myeloma Relapsed (vs Rd) ──
    {
        'name': 'Relapsed Multiple Myeloma',
        'pico': {
            'P': 'Relapsed or newly diagnosed multiple myeloma',
            'I': 'Carfilzomib-Rd, Daratumumab-Rd',
            'C': 'Lenalidomide-Dexamethasone (Rd)',
            'O': 'Progression-free survival',
        },
        'trials': [
            {'nctId': 'NCT01080391', 'pmid': '25482145', 'title': 'ASPIRE (KRd vs Rd relapsed)',
             'authors': 'Stewart AK', 'year': '2015', 'source': 'ctgov'},
            {'nctId': 'NCT02252172', 'pmid': '31141632', 'title': 'MAIA (DRd vs Rd frontline)',
             'authors': 'Facon T', 'year': '2019', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'progression',
        'effect_type': 'HR',
        'common_comparator': 'Rd',
        'norm_map': {
            'carfilzomib': 'KRd',
            'daratumumab': 'DRd',
            'lenalidomide': 'Rd',
            'dexamethasone': 'Rd',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'Both KRd and DRd improve PFS vs Rd',
    },
    # ── Topic 7: CLL First-Line ──
    {
        'name': 'CLL First-Line Treatment',
        'pico': {
            'P': 'Previously untreated chronic lymphocytic leukemia',
            'I': 'Ibrutinib, Venetoclax, Acalabrutinib',
            'C': 'Chlorambucil-based or Bendamustine-Rituximab',
            'O': 'Progression-free survival',
        },
        'trials': [
            {'nctId': 'NCT02264574', 'pmid': '30522969', 'title': 'iLLUMINATE (Ibrutinib+Obin vs Chlor+Obin)',
             'authors': 'Moreno C', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02475681', 'pmid': '32305093', 'title': 'ELEVATE-TN (Acalab+Obin vs Chlor+Obin)',
             'authors': 'Sharman JP', 'year': '2020', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'progression',
        'effect_type': 'HR',
        'common_comparator': 'Chlor+Obin',
        'norm_map': {
            'acalabrutinib': 'Acalab+Obin',  # MUST come before 'ibrutinib' (substring)
            'ibrutinib': 'Ibrutinib+Obin',
            'chlorambucil': 'Chlor+Obin',
            'obinutuzumab': 'Chlor+Obin',  # Both trials use CLB+OB as comparator
            'ibr': 'Ibrutinib+Obin',       # Abbreviated arm labels (IBR + OB)
            'clb': 'Chlor+Obin',           # Abbreviated arm labels (CLB + OB)
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'Both BTK inhibitor combos improve PFS vs chemoimmunotherapy',
    },
    # ── Topic 8: Ovarian Cancer PARP Maintenance ──
    {
        'name': 'Ovarian Cancer PARP Maintenance',
        'pico': {
            'P': 'Platinum-sensitive relapsed ovarian cancer',
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
        'benchmark_note': 'All 3 PARPi improve PFS vs placebo (HR 0.27-0.38 in BRCA+)',
    },
    # ── Topic 9: Gastric/GEJ First-Line ICI ──
    # CheckMate 649 + KEYNOTE-859: both 1L gastric ICI+Chemo vs Chemo (has_results=true)
    {
        'name': 'Gastric/GEJ First-Line Immunotherapy',
        'pico': {
            'P': 'Advanced gastric or GEJ adenocarcinoma',
            'I': 'ICI + chemotherapy (pembrolizumab, nivolumab)',
            'C': 'Chemotherapy alone',
            'O': 'Overall survival',
        },
        'trials': [
            {'nctId': 'NCT03675737', 'pmid': '37875143', 'title': 'KEYNOTE-859 (Pembro+Chemo vs Chemo)',
             'authors': 'Rha SY', 'year': '2023', 'source': 'ctgov'},
            {'nctId': 'NCT02872116', 'pmid': '34102137', 'title': 'CheckMate 649 (Nivo+Chemo vs Chemo)',
             'authors': 'Janjigian YY', 'year': '2021', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'overall survival',
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            'pembrolizumab': 'Pembro+Chemo',
            'ipilimumab': 'Nivo+Ipi',       # Check before nivolumab (CM649 has 3 arms)
            'nivolumab': 'Nivo+Chemo',
            'ono-4538': 'Nivo+Chemo',
            'xelox': 'Chemo',
            'folfox': 'Chemo',
            'placebo': 'Chemo',
            'oxaliplatin': 'Chemo',
            'capecitabine': 'Chemo',
            'fluorouracil': 'Chemo',
            'cisplatin': 'Chemo',
            'chemotherapy': 'Chemo',
        },
        'expect_favor_treatment': True,
        'benchmark_note': 'ICI+chemo improves OS in PD-L1+ gastric cancer (CM649 HR 0.71, KN859 HR 0.78)',
    },
    # ── Topic 10: NSCLC First-Line ICI+Chemo ──
    {
        'name': 'NSCLC First-Line ICI Combos',
        'pico': {
            'P': 'Metastatic non-squamous NSCLC',
            'I': 'ICI + platinum-doublet chemotherapy',
            'C': 'Platinum-doublet chemotherapy alone',
            'O': 'Overall survival or PFS',
        },
        'trials': [
            {'nctId': 'NCT02657434', 'pmid': '33333328', 'title': 'IMpower132 (Atezo+Chemo)',
             'authors': 'Nishio M', 'year': '2021', 'source': 'ctgov'},
            {'nctId': 'NCT02220894', 'pmid': '30955977', 'title': 'KEYNOTE-042 (Pembro mono vs Chemo)',
             'authors': 'Mok TSK', 'year': '2019', 'source': 'ctgov'},
            {'nctId': 'NCT02142738', 'pmid': '27718847', 'title': 'KEYNOTE-024 (Pembro mono vs Chemo, PD-L1>50%)',
             'authors': 'Reck M', 'year': '2016', 'source': 'ctgov'},
        ],
        'outcome_keyword': 'survival',
        'effect_type': 'HR',
        'common_comparator': 'Chemo',
        'norm_map': {
            'atezolizumab': 'Atezo+Chemo',
            'pembrolizumab': 'Pembrolizumab',
            'carboplatin': 'Chemo',
            'cisplatin': 'Chemo',
            'pemetrexed': 'Chemo',
            'paclitaxel': 'Chemo',
            'gemcitabine': 'Chemo',
            'chemotherapy': 'Chemo',   # catches "SOC Chemotherapy", "Chemotherapy"
            'placebo': 'Chemo',        # catches placebo comparator labels
        },
        'expect_favor_treatment': None,  # Pembro mono vs Chemo: OS favors Pembro, but PFS may not
        'benchmark_note': 'ICI regimens improve OS vs chemo in PD-L1+ NSCLC',
    },
]


# ═══════════════════════════════════════════════════════════════════
# MAIN TEST RUNNER
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
                        source: o.source, isPrimary: o.isPrimary
                    });
                }
            }
            return JSON.stringify(out);
        """))

        # Step 4: Select outcomes matching the topic
        outcome_kw = topic['outcome_keyword']
        effect_type = topic['effect_type']
        driver.execute_script(f"""
            var kw = {json.dumps(outcome_kw)}.toLowerCase();
            var et = {json.dumps(effect_type)};
            // Uncheck all
            for (var t of _extractionResults) {{
                for (var o of (t.outcomes||[])) o.checked = false;
            }}
            for (var t of _extractionResults) {{
                var matches = [];
                for (var o of (t.outcomes||[])) {{
                    if (o.effectType !== et) continue;
                    var title = (o.outcomeTitle || '').toLowerCase();
                    if (title.indexOf(kw) >= 0 || kw === '') matches.push(o);
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
            result['issues'].append(f'TOO_FEW_SELECTED: Only {n_selected} outcomes matched keyword "{outcome_kw}" (need >=2)')
            # Broader fallback: any HR with valid estimate
            driver.execute_script("""
                for (var t of _extractionResults) {
                    var hasChecked = false;
                    for (var o of (t.outcomes||[])) { if (o.checked) hasChecked = true; }
                    if (!hasChecked) {
                        // Try any HR
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
                    # Print available outcomes for diagnosis
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
                // Check direct substring matches
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
        # Flag if any treatment name looks un-normalized (very long or contains generic terms)
        for nm in norm_names:
            for side in ['t1', 't2']:
                name = nm[side]
                if len(name) > 30:
                    result['issues'].append(f'LONG_NAME: {nm["nct"]} {side}="{name[:50]}" (may need normalization)')

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

        # Capture norm warnings
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
            # Check if one side is the comparator
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

        # Validation
        if topic.get('expect_favor_treatment') and result['drug_vs_ref']:
            for dvr in result['drug_vs_ref']:
                hr = dvr.get('hr', dvr.get('effect'))
                if hr is not None and hr > 1.0:
                    result['issues'].append(f'UNEXPECTED_DIRECTION: {dvr["drug"]} HR={hr:.3f} (expected <1)')

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

    results = []
    try:
        print('=' * 80)
        print('10-TOPIC NMA PIPELINE STRESS TEST')
        print('=' * 80)

        for i, topic in enumerate(TOPICS):
            print(f'\n{"="*80}')
            print(f'TOPIC {i+1}/10: {topic["name"]}')
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

            if result['issues']:
                print(f'  Issues ({len(result["issues"])}):')
                for iss in result['issues']:
                    print(f'    [!] {iss}')

        # ═══════════════════════════════════════════════════════════════
        # FINAL REPORT
        # ═══════════════════════════════════════════════════════════════
        print(f'\n\n{"="*80}')
        print('FINAL REPORT: 10-TOPIC NMA STRESS TEST')
        print(f'{"="*80}')

        pass_count = sum(1 for r in results if r['status'] == 'PASS')
        fail_count = len(results) - pass_count

        print(f'\n  PASS: {pass_count}/10')
        print(f'  FAIL: {fail_count}/10')

        # Summary table
        print(f'\n  {"#":<3} {"Topic":<40} {"Status":<12} {"Tri":<4} {"Out":<4} {"Sel":<4} {"nT":<4} {"nE":<4} {"Issues":<5}')
        print(f'  {"-"*3} {"-"*40} {"-"*12} {"-"*4} {"-"*4} {"-"*4} {"-"*4} {"-"*4} {"-"*5}')
        for i, r in enumerate(results):
            print(f'  {i+1:<3} {r["name"]:<40} {r["status"]:<12} {r["n_trials_extracted"]:<4} '
                  f'{r["n_outcomes_extracted"]:<4} {r["n_outcomes_selected"]:<4} '
                  f'{r["nma_treatments"]:<4} {r["nma_edges"]:<4} {len(r["issues"]):<5}')

        # All issues aggregated
        all_issues = []
        for r in results:
            for iss in r['issues']:
                all_issues.append(f'{r["name"]}: {iss}')

        if all_issues:
            print(f'\n  ALL ISSUES ({len(all_issues)}):')
            for iss in all_issues:
                print(f'    {iss}')

            # Categorize issues
            categories = {}
            for iss in all_issues:
                cat = iss.split(': ', 2)[1].split(':')[0] if ': ' in iss else 'OTHER'
                categories.setdefault(cat, []).append(iss)
            print(f'\n  ISSUE CATEGORIES:')
            for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
                print(f'    {cat}: {len(items)} occurrences')

        # Treatment normalization quality
        print(f'\n  TREATMENT NORMALIZATION QUALITY:')
        for r in results:
            if r['raw_treatment_names']:
                bad_names = [rn for rn in r['raw_treatment_names']
                             if len(rn['t1']) > 25 or len(rn['t2']) > 25]
                if bad_names:
                    print(f'    {r["name"]}: {len(bad_names)} long names need better normalization')

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
