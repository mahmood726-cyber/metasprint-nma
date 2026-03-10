"""
Real-world validation: SGLT2i kidney outcomes meta-analysis.
Auto-extracts from CT.gov, selects primary outcomes, runs MetaSprint NMA engine,
compares pooled HR to published Lancet 2022 SMART-C benchmark.

Published benchmark (Nuffield SGLT2i Meta-Analysis Cardio-Renal Trialists):
  Kidney disease progression: HR 0.63 (95% CI 0.58-0.69)
  Source: Lancet 2022; 400: 1788-801. PMID 36351458

Key trials (primary kidney composite endpoint):
  CREDENCE (NCT02065791) - Canagliflozin - HR 0.70 (0.59-0.82)
  DAPA-CKD  (NCT03036150) - Dapagliflozin  - HR 0.61 (0.51-0.72) [primary composite]
  EMPA-KIDNEY (NCT03594110) - Empagliflozin - HR 0.72 (0.64-0.82) [from Lancet; CT.gov primary=0.72 0.59-0.89]
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

LANCET_POOLED = {'hr': 0.63, 'lo': 0.58, 'hi': 0.69}

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
        print('='*70)
        print('SGLT2i KIDNEY OUTCOMES: AUTO-EXTRACT + APP META-ANALYSIS')
        print('='*70)

        driver.get(FILE_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
        time.sleep(1)
        try:
            driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except Exception:
            pass

        # Step 1: Create project with PICO
        print('\n[1] Creating project...')
        driver.execute_script("""
            var nameInput = document.getElementById('projectName');
            if (nameInput) { nameInput.value = 'SGLT2i Kidney Outcomes'; nameInput.dispatchEvent(new Event('input')); }
            var pInput = document.getElementById('picoP');
            var iInput = document.getElementById('picoI');
            var cInput = document.getElementById('picoC');
            var oInput = document.getElementById('picoO');
            if(pInput) pInput.value = 'Chronic kidney disease';
            if(iInput) iInput.value = 'SGLT2 inhibitor';
            if(cInput) cInput.value = 'Placebo';
            if(oInput) oInput.value = 'Kidney disease progression';
            if(typeof createProject==='function') createProject();
        """)
        time.sleep(1)

        # Step 2: Inject search results and run auto-extract
        print('[2] Injecting search results for 3 landmark trials...')
        driver.execute_script("""
            switchPhase('search');
            searchResultsCache = [
                { nctId: 'NCT02065791', pmid: '30990260', title: 'CREDENCE', authors: 'Perkovic V', year: '2019', doi: '10.1056/NEJMoa1811744', source: 'ctgov' },
                { nctId: 'NCT03036150', pmid: '32970396', title: 'DAPA-CKD', authors: 'Heerspink HJL', year: '2020', doi: '10.1056/NEJMoa2024816', source: 'ctgov' },
                { nctId: 'NCT03594110', pmid: '36331190', title: 'EMPA-KIDNEY', authors: 'EMPA-KIDNEY Group', year: '2023', doi: '10.1056/NEJMoa2204233', source: 'ctgov' }
            ];
            var aeRow = document.getElementById('autoExtractRow');
            if (aeRow) aeRow.style.display = 'block';
        """)
        time.sleep(0.5)

        print('[3] Running Auto-Extract (live CT.gov API calls)...')
        driver.execute_script("runAutoExtract()")

        for tick in range(90):
            time.sleep(2)
            running = driver.execute_script("return _autoExtractRunning")
            status = driver.execute_script("return document.getElementById('autoExtractStatus')?.textContent || ''")
            if tick % 5 == 0 or not running:
                print(f'    [{tick*2}s] {status}')
            if not running:
                break

        # Step 4: Check extraction & select primary outcomes only
        total = driver.execute_script("return _extractionResults.reduce(function(s,t){return s+t.outcomes.length},0)")
        primary = driver.execute_script("return _extractionResults.reduce(function(s,t){return s+t.outcomes.filter(function(o){return o.isPrimary}).length},0)")
        print(f'\n[4] Extracted {total} outcomes ({primary} marked PRIMARY)')

        # Print all outcomes per trial
        for ti in range(3):
            nct = driver.execute_script(f"return _extractionResults[{ti}]?.nctId||'?'")
            n_out = driver.execute_script(f"return _extractionResults[{ti}]?.outcomes?.length||0")
            print(f'    {nct}: {n_out} outcomes')
            for oi in range(min(n_out, 15)):
                o = json.loads(driver.execute_script(f"return JSON.stringify(_extractionResults[{ti}].outcomes[{oi}])"))
                p_tag = ' [PRIMARY]' if o.get('isPrimary') else ''
                print(f'      {o.get("effectType","?")} = {o.get("estimate","")} [{o.get("lowerCI","")}, {o.get("upperCI","")}]{p_tag} | {(o.get("outcomeTitle",""))[:55]}')

        # Click "Primary Only"
        if primary > 0:
            print(f'\n[5] Clicking "Primary Only" button ({primary} primary outcomes)...')
            driver.execute_script("selectPrimaryOnly()")
            time.sleep(0.5)
        else:
            print('\n[5] No PRIMARY markers from CT.gov. Manually selecting first outcome per trial...')
            driver.execute_script("""
                for (var t of _extractionResults) {
                    var first = true;
                    for (var o of t.outcomes) {
                        o.checked = first && o.effectType === 'HR';
                        if (o.checked) first = false;
                    }
                }
            """)

        checked = driver.execute_script("""
            var c = [];
            for (var t of _extractionResults) {
                for (var o of t.outcomes) {
                    if (o.checked) c.push({nct: t.nctId, type: o.effectType, est: o.estimate, lo: o.lowerCI, hi: o.upperCI, title: o.outcomeTitle});
                }
            }
            return JSON.stringify(c);
        """)
        selected = json.loads(checked)
        print(f'    Selected {len(selected)} outcomes for meta-analysis:')
        for s in selected:
            print(f'      {s["nct"]}: {s["type"]} = {s["est"]} [{s["lo"]}, {s["hi"]}] | {s["title"][:50]}')

        # Step 6: Accept into Extract table
        print(f'\n[6] Accepting selected outcomes -> Extract table...')
        driver.execute_script("acceptExtractedStudies()")
        time.sleep(1)

        n_studies = driver.execute_script("return extractedStudies?.length || 0")
        print(f'    {n_studies} studies in Extract table')

        # NMA engine requires: effectType, outcomeId, timepoint, treatment1, treatment2
        # Also: only 1 primary outcome per trial for clean meta
        driver.execute_script("""
            // De-duplicate: keep only first study per nctId (first primary)
            var seen = {};
            var keep = [];
            for (var s of extractedStudies) {
                var key = s.nctId || s.authorYear;
                if (!seen[key]) { seen[key] = true; keep.push(s); }
            }
            extractedStudies.length = 0;
            for (var s of keep) extractedStudies.push(s);
            // Set required fields
            for (var s of extractedStudies) {
                s.effectType = 'HR';
                s.outcomeId = 'Kidney composite';
                s.timepoint = 'End of study';
            }
        """)

        # Print final extract table
        studies_json = driver.execute_script("return JSON.stringify(extractedStudies)")
        studies = json.loads(studies_json)
        print('\n    Final Extract table:')
        for s in studies:
            print(f'    {s.get("authorYear","?")} | {s.get("treatment1","?")} vs {s.get("treatment2","?")} | '
                  f'HR = {s.get("effectEstimate","")} [{s.get("lowerCI","")}, {s.get("upperCI","")}] | '
                  f'source: {s.get("extractionSource","")}')

        # Step 7: Switch to Analyze and run
        print('\n[7] Running MetaSprint NMA analysis engine...')
        driver.execute_script("switchPhase('analyze')")
        time.sleep(1)

        # Save studies to IndexedDB and wait
        driver.execute_script("""
            (async function() {
                for (var s of extractedStudies) { await saveStudy(s); }
                window.__studiesSaved = true;
            })();
        """)
        for _ in range(20):
            if driver.execute_script("return window.__studiesSaved === true"):
                break
            time.sleep(0.5)
        time.sleep(0.5)

        # Disable strict publishable gates for this test
        driver.execute_script("""
            var gate = document.getElementById('publishableGateToggle');
            if (gate) gate.checked = false;
        """)

        # Debug: check what runAnalysis will see
        n_valid = driver.execute_script("""
            return extractedStudies.filter(function(s) {
                return s.effectEstimate !== null && s.lowerCI !== null && s.upperCI !== null;
            }).length;
        """)
        print(f'    Valid studies for analysis: {n_valid}')

        # Try calling engine directly (bypass loadStudies/IndexedDB)
        engine_result = driver.execute_script("""
            try {
                var valid = extractedStudies.filter(function(s) {
                    return s.effectEstimate !== null && s.lowerCI !== null && s.upperCI !== null;
                });
                if (valid.length < 2) return JSON.stringify({error: 'Need >=2 valid studies, got ' + valid.length});

                var network = buildNetworkGraph(valid);
                if (!network || network.nE === 0) return JSON.stringify({error: 'Empty network', nT: network?.nT, nE: network?.nE});

                var result = runFrequentistNMA(network, 0.95, {tau2Method: 'DL'});
                window.lastAnalysisResult = result;
                return JSON.stringify({
                    ok: true,
                    nT: result.nT, nE: result.nE,
                    tau2: result.tau2, I2: result.I2global,
                    Q: result.Qtotal, df: result.dfTotal,
                    treatments: result.treatments,
                    ref: result.refTreatment,
                    isRatio: result.isRatio,
                    d: Array.from(result.d || []),
                    pscores: result.pscores,
                    league: (result.leagueTable || []).map(function(e) {
                        return {t1:e.t1, t2:e.t2, eff:e.effect, lo:e.lo, hi:e.hi};
                    })
                });
            } catch(e) {
                return JSON.stringify({error: e.message || String(e), stack: (e.stack||'').slice(0,300)});
            }
        """)

        # Get analysis result
        result_json = driver.execute_script("""
            var r = window.lastAnalysisResult;
            if (!r) return null;
            return JSON.stringify({
                model: r.tau2Method || r.model,
                tau2: r.tau2,
                I2global: r.I2global,
                Qtotal: r.Qtotal,
                dfTotal: r.dfTotal,
                nT: r.nT,
                nE: r.nE,
                isRatio: r.isRatio,
                treatments: r.treatments,
                refTreatment: r.refTreatment,
                d: Array.from(r.d || []),
                leagueTable: (r.leagueTable || []).slice(0, 10),
                pscores: r.pscores
            });
        """)

        app_pooled = None
        if result_json:
            analysis = json.loads(result_json)
            print(f'\n[8] MetaSprint NMA result:')
            print(f'    Model: {analysis.get("model","?")}')
            print(f'    Treatments: {analysis.get("treatments",[])}')
            print(f'    Reference: {analysis.get("refTreatment","?")}')
            print(f'    nT={analysis.get("nT","?")}, nE={analysis.get("nE","?")}')
            print(f'    tau2: {analysis.get("tau2","?")}, I2: {analysis.get("I2global","?")}%')
            print(f'    Q: {analysis.get("Qtotal","?")}, df: {analysis.get("dfTotal","?")}')
            print(f'    isRatio: {analysis.get("isRatio","?")}')
            print(f'    d (log effects vs ref): {analysis.get("d",[])}')
            print(f'    P-scores: {analysis.get("pscores",[])}')

            lt = analysis.get('leagueTable', [])
            drug_vs_placebo = []
            if lt:
                print(f'\n    League table ({len(lt)} entries):')
                for entry in lt:
                    t1 = entry.get('t1','?')
                    t2 = entry.get('t2','?')
                    eff = entry.get('effect', entry.get('eff', '?'))
                    lo = entry.get('lo','?')
                    hi = entry.get('hi','?')
                    if analysis.get('isRatio') and isinstance(eff, (int,float)):
                        hr = math.exp(eff)
                        hr_lo = math.exp(lo) if isinstance(lo, (int,float)) else '?'
                        hr_hi = math.exp(hi) if isinstance(hi, (int,float)) else '?'
                        print(f'      {t1} vs {t2}: logHR={eff:.4f} -> HR={hr:.3f} [{hr_lo:.3f}, {hr_hi:.3f}]')
                        # Capture Drug vs Placebo comparisons
                        if 'placebo' in t2.lower() and 'placebo' not in t1.lower():
                            drug_vs_placebo.append({'drug': t1, 'hr': hr, 'lo': hr_lo, 'hi': hr_hi})
                    else:
                        print(f'      {t1} vs {t2}: {eff} [{lo}, {hi}]')

            if drug_vs_placebo:
                print(f'\n    Drug vs Placebo (NMA estimates):')
                for dvp in drug_vs_placebo:
                    print(f'      {dvp["drug"]}: HR {dvp["hr"]:.3f} ({dvp["lo"]:.3f}-{dvp["hi"]:.3f})')
                # P-scores for ranking
                pscores = analysis.get('pscores', {})
                treatments = analysis.get('treatments', [])
                if pscores and treatments:
                    print(f'\n    P-score ranking (1.0 = best):')
                    scored = [(treatments[int(k)], pscores[k]) for k in pscores if int(k) < len(treatments)]
                    scored.sort(key=lambda x: -x[1])
                    for name, ps in scored:
                        print(f'      {name}: {ps:.3f}')
                app_pooled = drug_vs_placebo
        else:
            print('\n[8] No analysis result. Checking for errors...')
            errors = driver.execute_script("""
                var logs = [];
                if (typeof _analysisErrors !== 'undefined') logs = _analysisErrors;
                return JSON.stringify(logs);
            """)
            print(f'    Errors: {errors}')

            # Check console
            browser_logs = driver.get_log('browser')
            severe = [l for l in browser_logs if l.get('level') == 'SEVERE'
                      and 'favicon' not in l.get('message','')
                      and 'Content Security' not in l.get('message','')]
            if severe:
                print(f'    Console errors:')
                for e in severe[:5]:
                    print(f'      {e["message"][:120]}')

        # Step 9: Manual inverse-variance meta for reference
        print('\n' + '='*70)
        print('COMPARISON')
        print('='*70)

        # Use the values actually selected (from extract table)
        print(f'\n--- Studies used (from auto-extract) ---')
        manual_studies = []
        for s in studies:
            ee = s.get('effectEstimate')
            lo = s.get('lowerCI')
            hi = s.get('upperCI')
            if ee is not None and lo is not None and hi is not None:
                log_hr = math.log(ee)
                se = (math.log(hi) - math.log(lo)) / (2 * 1.96)
                manual_studies.append({'name': s.get('authorYear','?'), 'log_hr': log_hr, 'se': se, 'hr': ee, 'lo': lo, 'hi': hi})
                print(f'    {s.get("authorYear","?")}: HR {ee} [{lo}, {hi}] -> logHR {log_hr:.4f}, SE {se:.4f}')

        if len(manual_studies) >= 2:
            weights = [1/s['se']**2 for s in manual_studies]
            w_sum = sum(weights)
            pooled_log = sum(w*s['log_hr'] for w, s in zip(weights, manual_studies)) / w_sum
            pooled_se = math.sqrt(1/w_sum)
            fe_hr = math.exp(pooled_log)
            fe_lo = math.exp(pooled_log - 1.96*pooled_se)
            fe_hi = math.exp(pooled_log + 1.96*pooled_se)

            Q = sum(w*(s['log_hr'] - pooled_log)**2 for w, s in zip(weights, manual_studies))
            k = len(manual_studies)
            I2 = max(0, (Q - (k-1))/Q * 100) if Q > k-1 else 0.0

            # DL random effects
            C = w_sum - sum(w**2 for w in weights) / w_sum
            tau2 = max(0, (Q - (k-1)) / C)
            if tau2 > 0:
                w_re = [1/(s['se']**2 + tau2) for s in manual_studies]
                w_re_sum = sum(w_re)
                re_log = sum(w*s['log_hr'] for w, s in zip(w_re, manual_studies)) / w_re_sum
                re_se = math.sqrt(1/w_re_sum)
                dl_hr = math.exp(re_log)
                dl_lo = math.exp(re_log - 1.96*re_se)
                dl_hi = math.exp(re_log + 1.96*re_se)
            else:
                dl_hr, dl_lo, dl_hi = fe_hr, fe_lo, fe_hi

            print(f'\n--- Pooled results ---')
            print(f'    Manual pairwise FE:   HR {fe_hr:.3f} ({fe_lo:.3f}-{fe_hi:.3f}) | Q={Q:.2f} I2={I2:.1f}%')
            print(f'    Manual pairwise DL:   HR {dl_hr:.3f} ({dl_lo:.3f}-{dl_hi:.3f}) | tau2={tau2:.4f}')
            if app_pooled and isinstance(app_pooled, list):
                print(f'    App NMA engine (drug vs Placebo):')
                for dvp in app_pooled:
                    print(f'      {dvp["drug"]}: HR {dvp["hr"]:.3f} ({dvp["lo"]:.3f}-{dvp["hi"]:.3f})')
                # Compare individual NMA estimates to input data
                print(f'\n    NMA vs Input comparison:')
                for s, dvp in zip(manual_studies, app_pooled):
                    input_hr = s['hr']
                    nma_hr = dvp['hr']
                    pct = abs(nma_hr - input_hr) / input_hr * 100
                    print(f'      {s["name"]}: input HR {input_hr:.3f} vs NMA HR {nma_hr:.3f} ({pct:.1f}% diff)')
            print(f'    Lancet 2022 (13 trials): HR {LANCET_POOLED["hr"]:.3f} ({LANCET_POOLED["lo"]:.3f}-{LANCET_POOLED["hi"]:.3f})')

            print(f'\n--- Validation ---')
            all_favor = all(s['hr'] < 1 for s in manual_studies)
            print(f'    Direction: {"CONCORDANT" if all_favor else "DISCORDANT"} (all favor SGLT2i)')
            ci_overlap = fe_lo <= LANCET_POOLED['hi'] and fe_hi >= LANCET_POOLED['lo']
            print(f'    CI overlap with Lancet: {"YES" if ci_overlap else "NO"}')
            gap = abs(fe_hr - LANCET_POOLED['hr']) / LANCET_POOLED['hr'] * 100
            print(f'    Point estimate gap (FE vs Lancet): {gap:.1f}%')
            if app_pooled and isinstance(app_pooled, list):
                # Validate NMA engine reproduces input HRs (star network, each drug has 1 study)
                all_close = all(
                    abs(dvp['hr'] - s['hr']) / s['hr'] < 0.02
                    for s, dvp in zip(manual_studies, app_pooled)
                )
                if all_close:
                    print(f'    NMA ENGINE VALIDATED: reproduces input HRs within 2%')
                else:
                    print(f'    NMA ENGINE: some estimates differ >2% from input (expected for network effects)')
        else:
            print('\n    [!] Not enough studies for pooling')

        print(f'\n{"="*70}')
        print(f'COMPLETE')
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
