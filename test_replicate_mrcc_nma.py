"""
Replication: First-line mRCC ICI Network Meta-Analysis
Benchmark: Yanagisawa et al. 2024 (Cancer Immunol Immunother)
DOI: 10.1007/s00262-023-03621-1

6 Phase 3 RCTs, all ICI-combos vs Sunitinib (star network):
  1. CheckMate 214  (NCT02231749) - Nivo+Ipi vs Sunitinib
  2. KEYNOTE-426    (NCT02853331) - Pembro+Axi vs Sunitinib
  3. CheckMate 9ER  (NCT03141177) - Nivo+Cabo vs Sunitinib
  4. JAVELIN Renal  (NCT02684006) - Avelumab+Axi vs Sunitinib
  5. CLEAR          (NCT02811861) - Pembro+Lenva vs Sunitinib
  6. IMmotion151    (NCT02420821) - Atez+Bev vs Sunitinib

Approach: Use MetaSprint NMA app auto-extract from CT.gov only (no PDFs).
Compare PFS HR rankings to published NMA.

Published PFS HR ranking (Yanagisawa NMA, SUCRA):
  1. Pembro+Lenva (best PFS, SUCRA 99%)
  2. Nivo+Cabo
  3. Pembro+Axi
  4. Nivo+Ipi
  5. Atez+Bev (near Sunitinib)
"""
import io, sys, os, time, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metasprint-nma.html')
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')

# 6 trials for mRCC first-line NMA
TRIALS = [
    {'nctId': 'NCT02231749', 'pmid': '29562145', 'title': 'CheckMate 214 (Nivo+Ipi)',
     'authors': 'Motzer RJ', 'year': '2018', 'doi': '10.1056/NEJMoa1712126', 'source': 'ctgov'},
    {'nctId': 'NCT02853331', 'pmid': '30779529', 'title': 'KEYNOTE-426 (Pembro+Axi)',
     'authors': 'Rini BI', 'year': '2019', 'doi': '10.1056/NEJMoa1816714', 'source': 'ctgov'},
    {'nctId': 'NCT03141177', 'pmid': '33657295', 'title': 'CheckMate 9ER (Nivo+Cabo)',
     'authors': 'Choueiri TK', 'year': '2021', 'doi': '10.1056/NEJMoa2026982', 'source': 'ctgov'},
    {'nctId': 'NCT02684006', 'pmid': '30779531', 'title': 'JAVELIN Renal 101 (Ave+Axi)',
     'authors': 'Motzer RJ', 'year': '2019', 'doi': '10.1056/NEJMoa1816047', 'source': 'ctgov'},
    {'nctId': 'NCT02811861', 'pmid': '33616314', 'title': 'CLEAR (Pembro+Lenva)',
     'authors': 'Motzer RJ', 'year': '2021', 'doi': '10.1056/NEJMoa2035716', 'source': 'ctgov'},
    {'nctId': 'NCT02420821', 'pmid': '31079938', 'title': 'IMmotion151 (Atez+Bev)',
     'authors': 'Rini BI', 'year': '2019', 'doi': '10.1016/S0140-6736(19)32008-2', 'source': 'ctgov'},
]

# Published PFS ranking from Yanagisawa NMA (SUCRA for PFS)
PUBLISHED_PFS_RANKING = [
    'Pembro+Lenva',   # CLEAR — best PFS
    'Nivo+Cabo',      # CheckMate 9ER
    'Pembro+Axi',     # KEYNOTE-426
    'Nivo+Ipi',       # CheckMate 214
    'Atez+Bev',       # IMmotion151
    'Sunitinib',      # reference
]


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

    try:
        print('=' * 70)
        print('mRCC FIRST-LINE ICI NMA REPLICATION')
        print('Yanagisawa et al. 2024, Cancer Immunol Immunother')
        print('=' * 70)

        driver.get(FILE_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
        time.sleep(1)
        try:
            driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except Exception:
            pass

        # Step 1: Create project
        print('\n[1] Creating mRCC NMA project...')
        driver.execute_script("""
            var nameInput = document.getElementById('projectName');
            if (nameInput) { nameInput.value = 'mRCC First-Line ICI NMA'; nameInput.dispatchEvent(new Event('input')); }
            var pInput = document.getElementById('picoP');
            var iInput = document.getElementById('picoI');
            var cInput = document.getElementById('picoC');
            var oInput = document.getElementById('picoO');
            if(pInput) pInput.value = 'Advanced/metastatic renal cell carcinoma';
            if(iInput) iInput.value = 'ICI-based combinations';
            if(cInput) cInput.value = 'Sunitinib';
            if(oInput) oInput.value = 'Progression-free survival';
            if(typeof createProject==='function') createProject();
        """)
        time.sleep(1)

        # Step 2: Inject search results for 6 trials
        print('[2] Injecting 6 landmark RCTs...')
        trials_json = json.dumps(TRIALS)
        driver.execute_script(f"""
            switchPhase('search');
            searchResultsCache = {trials_json};
            var aeRow = document.getElementById('autoExtractRow');
            if (aeRow) aeRow.style.display = 'block';
        """)
        time.sleep(0.5)

        # Step 3: Run auto-extract
        print('[3] Running Auto-Extract (live CT.gov API calls for 6 trials)...')
        print('    This may take 30-60 seconds...')
        driver.execute_script("runAutoExtract()")

        for tick in range(120):
            time.sleep(2)
            running = driver.execute_script("return _autoExtractRunning")
            status = driver.execute_script("return document.getElementById('autoExtractStatus')?.textContent || ''")
            if tick % 5 == 0 or not running:
                print(f'    [{tick*2}s] {status}')
            if not running:
                break

        # Step 4: Examine extraction results
        n_trials = driver.execute_script("return _extractionResults.length")
        total_outcomes = driver.execute_script(
            "return _extractionResults.reduce(function(s,t){return s+t.outcomes.length},0)")
        print(f'\n[4] Extracted from {n_trials} trials, {total_outcomes} total outcomes')

        # Print all outcomes per trial
        all_trial_data = []
        for ti in range(n_trials):
            trial_info = json.loads(driver.execute_script(f"""
                var t = _extractionResults[{ti}];
                return JSON.stringify({{
                    nctId: t.nctId, title: t.title, authorYear: t.authorYear,
                    nOutcomes: t.outcomes.length,
                    outcomes: t.outcomes.map(function(o) {{
                        return {{
                            effectType: o.effectType, estimate: o.estimate,
                            lowerCI: o.lowerCI, upperCI: o.upperCI,
                            isPrimary: o.isPrimary, outcomeType: o.outcomeType,
                            outcomeTitle: (o.outcomeTitle||'').substring(0,70),
                            source: o.source
                        }};
                    }})
                }});
            """))
            all_trial_data.append(trial_info)
            print(f'\n    {trial_info["nctId"]} ({trial_info["authorYear"]}): {trial_info["nOutcomes"]} outcomes')
            for o in trial_info['outcomes']:
                p_tag = ' [PRIMARY]' if o.get('isPrimary') else ''
                src = f' ({o.get("source","?")})' if o.get('source') else ''
                print(f'      {o["effectType"]} = {o["estimate"]} [{o["lowerCI"]}, {o["upperCI"]}]{p_tag}{src}')
                print(f'        {o["outcomeTitle"]}')

        # Step 5: Select PFS outcomes
        # Strategy: For each trial, find the ITT PFS HR vs Sunitinib
        # Special cases:
        #   - CLEAR (NCT02811861): 3 arms — select Pembro+Lenva (lowest PFS HR), not Lenva+Everolimus
        #   - CheckMate 214: intermediate/poor-risk PFS is the primary endpoint
        #   - JAVELIN: PD-L1+ population is primary — prefer "irrespective of PD-L1" for ITT
        print('\n[5] Selecting PFS HR outcomes (1 per trial, ITT preferred)...')
        driver.execute_script("""
            // Uncheck all first
            for (var t of _extractionResults) {
                for (var o of t.outcomes) { o.checked = false; }
            }
            for (var t of _extractionResults) {
                var pfsHRs = [];
                for (var o of t.outcomes) {
                    if (o.effectType !== 'HR') continue;
                    var title = (o.outcomeTitle || '').toLowerCase();
                    var isPFS = title.indexOf('progression') >= 0 || title.indexOf('pfs') >= 0;
                    if (isPFS) pfsHRs.push(o);
                }
                if (pfsHRs.length === 0) {
                    // Fallback: first primary HR
                    for (var o of t.outcomes) {
                        if (o.effectType === 'HR' && o.isPrimary) { o.checked = true; break; }
                    }
                    continue;
                }

                var nct = t.nctId;

                // CLEAR (NCT02811861): 2 PFS primaries — pick Pembro+Lenva (lower HR = 0.39)
                if (nct === 'NCT02811861') {
                    var best = pfsHRs[0];
                    for (var o of pfsHRs) {
                        if (o.estimate < best.estimate) best = o;
                    }
                    best.checked = true;
                    continue;
                }

                // JAVELIN (NCT02684006): prefer "irrespective of PD-L1" BICR
                if (nct === 'NCT02684006') {
                    var ittPFS = null;
                    for (var o of pfsHRs) {
                        var t2 = (o.outcomeTitle||'').toLowerCase();
                        if (t2.indexOf('irrespective') >= 0 && t2.indexOf('bicr') >= 0) { ittPFS = o; break; }
                        if (t2.indexOf('irrespective') >= 0 && !ittPFS) ittPFS = o;
                    }
                    if (ittPFS) { ittPFS.checked = true; continue; }
                }

                // Default: prefer primary PFS, else first PFS
                var best = pfsHRs[0];
                for (var o of pfsHRs) {
                    if (o.isPrimary && !best.isPrimary) best = o;
                }
                best.checked = true;
            }
            renderExtractionReview();
        """)
        time.sleep(0.5)

        # Print selected outcomes
        selected = json.loads(driver.execute_script("""
            var c = [];
            for (var t of _extractionResults) {
                for (var o of t.outcomes) {
                    if (o.checked) c.push({
                        nct: t.nctId, authorYear: t.authorYear,
                        type: o.effectType, est: o.estimate,
                        lo: o.lowerCI, hi: o.upperCI,
                        title: (o.outcomeTitle||'').substring(0,60)
                    });
                }
            }
            return JSON.stringify(c);
        """))
        print(f'    Selected {len(selected)} outcomes for NMA:')
        for s in selected:
            print(f'      {s["nct"]} ({s["authorYear"]}): {s["type"]} = {s["est"]} [{s["lo"]}, {s["hi"]}]')
            print(f'        {s["title"]}')

        if len(selected) < 3:
            print('\n    [!] Too few outcomes extracted. Aborting NMA.')
            print('    This may mean CT.gov structured results lack HR data for some trials.')
            # Still print what we got for diagnosis
            driver.quit()
            return 1

        # Step 6: Accept into extract table
        print(f'\n[6] Accepting {len(selected)} studies -> Extract table...')
        driver.execute_script("acceptExtractedStudies()")
        time.sleep(1)

        n_studies = driver.execute_script("return extractedStudies?.length || 0")
        print(f'    {n_studies} studies in Extract table')

        # Deduplicate, normalize treatment names, set required fields
        driver.execute_script("""
            var seen = {};
            var keep = [];
            for (var s of extractedStudies) {
                var key = s.nctId || s.authorYear;
                if (!seen[key]) { seen[key] = true; keep.push(s); }
            }
            extractedStudies.length = 0;
            for (var s of keep) extractedStudies.push(s);

            // Normalize treatment names: merge all Sunitinib variants
            function normTreat(name) {
                var n = (name || '').trim();
                var lo = n.toLowerCase();
                // Sunitinib variants
                if (lo.indexOf('sunitinib') >= 0 || lo === 'monotherapy') return 'Sunitinib';
                // Standardize combo names
                if (lo.indexOf('nivolumab') >= 0 && lo.indexOf('ipilimumab') >= 0) return 'Nivo+Ipi';
                if (lo.indexOf('pembrolizumab') >= 0 && lo.indexOf('axitinib') >= 0) return 'Pembro+Axi';
                if (lo.indexOf('nivolumab') >= 0 && lo.indexOf('cabozantinib') >= 0) return 'Nivo+Cabo';
                if (lo.indexOf('avelumab') >= 0 && lo.indexOf('axitinib') >= 0) return 'Ave+Axi';
                if (lo.indexOf('lenvatinib') >= 0 && lo.indexOf('pembrolizumab') >= 0) return 'Pembro+Lenva';
                if (lo.indexOf('pembrolizumab') >= 0 && lo.indexOf('lenvatinib') >= 0) return 'Pembro+Lenva';
                if (lo.indexOf('lenvatinib') >= 0 && lo.indexOf('everolimus') >= 0) return 'Lenva+Everolimus';
                if (lo.indexOf('atezolizumab') >= 0 && lo.indexOf('bevacizumab') >= 0) return 'Atez+Bev';
                // Fallback: try CT.gov arm labels
                if (lo.indexOf('doublet') >= 0) return 'Nivo+Cabo';  // CheckMate 9ER labels
                return n;
            }
            for (var s of extractedStudies) {
                s.treatment1 = normTreat(s.treatment1);
                s.treatment2 = normTreat(s.treatment2);
                s.effectType = 'HR';
                s.outcomeId = 'PFS';
                s.timepoint = 'Primary analysis';
            }
        """)

        # Print final extract table
        studies = json.loads(driver.execute_script("return JSON.stringify(extractedStudies)"))
        print(f'\n    Final Extract table ({len(studies)} studies):')
        for s in studies:
            t1 = s.get('treatment1', '?')
            t2 = s.get('treatment2', '?')
            ee = s.get('effectEstimate', '?')
            lo = s.get('lowerCI', '?')
            hi = s.get('upperCI', '?')
            print(f'    {s.get("authorYear","?"):20s} | {t1} vs {t2} | HR {ee} [{lo}, {hi}]')

        # Step 7: Run NMA engine
        print('\n[7] Running MetaSprint NMA engine...')
        driver.execute_script("switchPhase('analyze')")
        time.sleep(1)

        # Debug: verify treatment names are normalized before engine call
        debug_names = json.loads(driver.execute_script("""
            return JSON.stringify(extractedStudies.map(function(s) {
                return {t1: s.treatment1, t2: s.treatment2, ee: s.effectEstimate};
            }));
        """))
        print('    Treatment names pre-engine:')
        for d in debug_names:
            print(f'      {d["t1"]} vs {d["t2"]} (HR={d["ee"]})')

        # Run engine directly — normalize treatment names inline to prevent reload corruption
        engine_result = json.loads(driver.execute_script("""
            try {
                // Re-normalize treatment names (switchPhase may reload from storage)
                function normT(name) {
                    var n = (name || '').trim(), lo = n.toLowerCase();
                    if (lo.indexOf('sunitinib') >= 0 || lo === 'monotherapy') return 'Sunitinib';
                    if (lo.indexOf('nivolumab') >= 0 && lo.indexOf('ipilimumab') >= 0) return 'Nivo+Ipi';
                    if (lo.indexOf('pembrolizumab') >= 0 && lo.indexOf('axitinib') >= 0) return 'Pembro+Axi';
                    if (lo.indexOf('nivolumab') >= 0 && lo.indexOf('cabozantinib') >= 0) return 'Nivo+Cabo';
                    if (lo.indexOf('cabozantinib') >= 0 && lo.indexOf('nivolumab') >= 0) return 'Nivo+Cabo';
                    if (lo.indexOf('avelumab') >= 0 && lo.indexOf('axitinib') >= 0) return 'Ave+Axi';
                    if (lo.indexOf('lenvatinib') >= 0 && lo.indexOf('pembrolizumab') >= 0) return 'Pembro+Lenva';
                    if (lo.indexOf('pembrolizumab') >= 0 && lo.indexOf('lenvatinib') >= 0) return 'Pembro+Lenva';
                    if (lo.indexOf('lenvatinib') >= 0 && lo.indexOf('everolimus') >= 0) return 'Lenva+Everolimus';
                    if (lo.indexOf('atezolizumab') >= 0 && lo.indexOf('bevacizumab') >= 0) return 'Atez+Bev';
                    if (lo === 'doublet') return 'Nivo+Cabo';
                    return n;
                }
                for (var s of extractedStudies) {
                    s.treatment1 = normT(s.treatment1);
                    s.treatment2 = normT(s.treatment2);
                }

                var valid = extractedStudies.filter(function(s) {
                    return s.effectEstimate !== null && s.lowerCI !== null && s.upperCI !== null;
                });
                if (valid.length < 2) return JSON.stringify({error: 'Need >=2 studies, got ' + valid.length});

                var network = buildNetworkGraph(valid);
                if (!network || network.nE === 0) return JSON.stringify({error: 'Empty network'});

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
                    leagueTable: (result.leagueTable || []).slice(0, 30)
                });
            } catch(e) {
                return JSON.stringify({error: e.message, stack: (e.stack||'').slice(0,300)});
            }
        """))

        if engine_result.get('error'):
            print(f'    NMA ENGINE ERROR: {engine_result["error"]}')
            if engine_result.get('stack'):
                print(f'    Stack: {engine_result["stack"][:200]}')
            driver.quit()
            return 1

        # Step 8: Display NMA results
        print(f'\n[8] NMA RESULTS:')
        print(f'    Treatments ({engine_result["nT"]}): {engine_result["treatments"]}')
        print(f'    Edges: {engine_result["nE"]}')
        print(f'    Reference: {engine_result["ref"]}')
        print(f'    tau2: {engine_result["tau2"]}, I2: {engine_result["I2"]}%')

        # League table: Drug vs Sunitinib
        lt = engine_result.get('leagueTable', [])
        drug_vs_suni = []
        if lt:
            print(f'\n    League table (Drug vs Sunitinib):')
            for entry in lt:
                t1 = entry.get('t1', '?')
                t2 = entry.get('t2', '?')
                eff = entry.get('effect', entry.get('eff', None))
                lo = entry.get('lo')
                hi = entry.get('hi')
                if engine_result.get('isRatio') and isinstance(eff, (int, float)):
                    try:
                        hr = math.exp(eff)
                        hr_lo = math.exp(lo) if isinstance(lo, (int, float)) else None
                        hr_hi = math.exp(hi) if isinstance(hi, (int, float)) else None
                    except (OverflowError, ValueError):
                        continue
                    if hr_lo is None or hr_hi is None:
                        continue
                    # Only show Drug vs Sunitinib
                    if 'sunitinib' in t2.lower() and 'sunitinib' not in t1.lower():
                        print(f'      {t1:30s} vs Sunitinib: HR {hr:.3f} ({hr_lo:.3f}-{hr_hi:.3f})')
                        drug_vs_suni.append({'drug': t1, 'hr': hr, 'lo': hr_lo, 'hi': hr_hi})

        # P-scores
        pscores = engine_result.get('pscores', {})
        treatments = engine_result.get('treatments', [])
        if pscores and treatments:
            print(f'\n    P-score ranking (1.0 = best PFS):')
            scored = []
            for k in pscores:
                idx = int(k)
                if idx < len(treatments):
                    scored.append((treatments[idx], pscores[k]))
            scored.sort(key=lambda x: -x[1])
            app_ranking = [name for name, ps in scored]
            for name, ps in scored:
                print(f'      {name:30s}: {ps:.3f}')

        # Step 9: Compare to published NMA
        print('\n' + '=' * 70)
        print('COMPARISON WITH PUBLISHED NMA')
        print('=' * 70)

        # Manual pairwise meta (inverse-variance FE)
        if len(studies) >= 2:
            manual_studies = []
            for s in studies:
                ee = s.get('effectEstimate')
                lo = s.get('lowerCI')
                hi = s.get('upperCI')
                if ee is not None and lo is not None and hi is not None and ee > 0 and lo > 0 and hi > 0:
                    log_hr = math.log(ee)
                    se = (math.log(hi) - math.log(lo)) / (2 * 1.96)
                    manual_studies.append({
                        'name': s.get('authorYear', '?'),
                        'log_hr': log_hr, 'se': se,
                        'hr': ee, 'lo': lo, 'hi': hi
                    })

            if manual_studies:
                print(f'\n--- Individual trial PFS HRs (extracted from CT.gov) ---')
                for ms in manual_studies:
                    print(f'    {ms["name"]:25s}: HR {ms["hr"]:.3f} ({ms["lo"]:.3f}-{ms["hi"]:.3f})')

        # Map trial author to drug name for matching
        TRIAL_DRUG_MAP = {
            'Motzer RJ 2018': 'Nivo+Ipi', 'Rini BI 2019': 'Pembro+Axi',
            'Choueiri TK 2021': 'Nivo+Cabo', 'Motzer RJ 2019': 'Ave+Axi',
            'Motzer RJ 2021': 'Pembro+Lenva',
        }
        # Find Atez+Bev (second Rini 2019)
        for ms in manual_studies:
            if ms['name'] == 'Rini BI 2019' and ms['name'] not in TRIAL_DRUG_MAP:
                pass  # handled below
        rini_count = 0
        for ms in manual_studies:
            if ms['name'] == 'Rini BI 2019':
                rini_count += 1
                if rini_count == 2:
                    ms['drug'] = 'Atez+Bev'
                else:
                    ms['drug'] = TRIAL_DRUG_MAP.get(ms['name'], ms['name'])
            else:
                ms['drug'] = TRIAL_DRUG_MAP.get(ms['name'], ms['name'])

        if drug_vs_suni:
            print(f'\n--- NMA vs Input comparison ---')
            for dvs in drug_vs_suni:
                match = next((ms for ms in manual_studies if ms.get('drug') == dvs['drug']), None)
                if match:
                    pct = abs(dvs['hr'] - match['hr']) / match['hr'] * 100
                    print(f'    {dvs["drug"]:20s}: input HR {match["hr"]:.3f} vs NMA HR {dvs["hr"]:.3f} ({pct:.1f}% diff)')
                else:
                    print(f'    {dvs["drug"]:20s}: NMA HR {dvs["hr"]:.3f}')

        # Compare rankings
        if pscores and treatments:
            print(f'\n--- Ranking comparison ---')
            print(f'    Published (Yanagisawa SUCRA):')
            for i, name in enumerate(PUBLISHED_PFS_RANKING):
                print(f'      {i+1}. {name}')
            print(f'    App NMA (P-scores):')
            for i, (name, ps) in enumerate(scored):
                print(f'      {i+1}. {name} (P={ps:.3f})')

            # Check concordance: do the top 2 match?
            pub_top2 = set(x.lower().replace('+', '').replace(' ', '') for x in PUBLISHED_PFS_RANKING[:2])
            app_top2 = set(x.lower().replace('+', '').replace(' ', '') for x in app_ranking[:2])
            # Fuzzy match
            concordance = len(pub_top2.intersection(app_top2))
            print(f'\n    Top-2 concordance: {concordance}/2')

        # Validation checks
        print(f'\n--- Validation ---')
        all_favor = all(dvs['hr'] < 1 for dvs in drug_vs_suni)
        print(f'    All ICI-combos favor treatment over Sunitinib: {"YES" if all_favor else "NO"}')

        if drug_vs_suni:
            best_drug = min(drug_vs_suni, key=lambda x: x['hr'])
            print(f'    Best PFS: {best_drug["drug"]} (HR {best_drug["hr"]:.3f})')
            # Published best PFS is Pembro+Lenva
            if 'lenva' in best_drug['drug'].lower() or 'clear' in best_drug['drug'].lower():
                print(f'    CONCORDANT with published NMA (Pembro+Lenva = best PFS)')
            else:
                print(f'    NOTE: Published NMA found Pembro+Lenva as best PFS')

        print(f'\n{"="*70}')
        print(f'REPLICATION COMPLETE')
        print(f'{"="*70}')

    except Exception as e:
        print(f'\nFATAL: {e}')
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

    return 0

if __name__ == '__main__':
    sys.exit(main())
