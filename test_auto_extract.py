"""
Selenium test for OA Auto-Extract feature.
Tests: parseAbstractEffects regex, extractionReview panel, accept flow, source badges.
"""
import io, sys, os, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metasprint-nma.html')
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')
TIMEOUT = 30
PASS = 0
FAIL = 0

def log_result(name, passed, detail=''):
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f'  [PASS] {name}' + (f' -- {detail}' if detail else ''))
    else:
        FAIL += 1
        print(f'  [FAIL] {name}' + (f' -- {detail}' if detail else ''))

def main():
    global PASS, FAIL
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1600,1200')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(3)

    try:
        driver.get(FILE_URL)
        WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
        time.sleep(1)
        # Dismiss onboarding
        try:
            driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except Exception:
            pass

        print('\n=== TEST: parseAbstractEffects ===')
        # Unit test the regex parser via JS
        result = driver.execute_script("""
            var r = parseAbstractEffects('The hazard ratio was HR 0.86, 95% CI 0.78-0.95, P=0.002. OR was 1.25 (95% CI 1.05 to 1.50).');
            return JSON.stringify(r);
        """)
        parsed = json.loads(result)
        log_result('AE-1: parseAbstractEffects returns results', len(parsed) >= 2, f'found {len(parsed)} effects')
        hr = next((p for p in parsed if p['effectType'] == 'HR'), None)
        log_result('AE-2: HR extracted correctly', hr and hr['estimate'] == 0.86, f'HR={hr}')
        log_result('AE-3: HR CI correct', hr and hr['lowerCI'] == 0.78 and hr['upperCI'] == 0.95)
        log_result('AE-4: HR p-value extracted', hr and hr['pValue'] == 0.002)
        orr = next((p for p in parsed if p['effectType'] == 'OR'), None)
        log_result('AE-5: OR extracted correctly', orr and orr['estimate'] == 1.25, f'OR={orr}')

        print('\n=== TEST: Edge cases ===')
        # Empty input
        empty = driver.execute_script("return parseAbstractEffects('').length")
        log_result('AE-6: Empty input returns 0', empty == 0)
        # No effect sizes
        none = driver.execute_script("return parseAbstractEffects('This is a study about diabetes.').length")
        log_result('AE-7: No-effect text returns 0', none == 0)
        # MD extraction
        md = driver.execute_script("""
            var r = parseAbstractEffects('Mean difference MD -3.5, 95% CI -5.2 to -1.8, p<0.001');
            return JSON.stringify(r);
        """)
        mdp = json.loads(md)
        log_result('AE-8: MD extracted', len(mdp) >= 1 and mdp[0]['effectType'] == 'MD', f'MD={mdp}')

        # RR extraction
        rr = driver.execute_script("""
            var r = parseAbstractEffects('relative risk RR 0.72, 95% CI 0.55-0.94');
            return JSON.stringify(r);
        """)
        rrp = json.loads(rr)
        log_result('AE-9: RR extracted', len(rrp) >= 1 and rrp[0]['effectType'] == 'RR', f'RR={rrp}')

        print('\n=== TEST: Auto-extract UI ===')
        # Check button exists but hidden
        ae_row = driver.execute_script("return document.getElementById('autoExtractRow')?.style.display")
        log_result('AE-10: Auto-extract row initially hidden', ae_row == 'none')

        # Check review panel exists but hidden
        rp = driver.execute_script("return document.getElementById('extractionReviewPanel')?.style.display")
        log_result('AE-11: Review panel initially hidden', rp == 'none')

        # Test renderExtractionReview with mock data
        driver.execute_script("""
            _extractionResults = [{
                nctId: 'NCT99999999', pmid: '12345678', title: 'Mock Trial',
                authorYear: 'TestAuthor 2024', doi: '', source: 'pubmed',
                outcomes: [{
                    effectType: 'HR', estimate: 0.75, lowerCI: 0.60, upperCI: 0.93,
                    pValue: 0.01, outcomeTitle: 'Primary MACE', source: 'pubmed',
                    evidence: { pubmed: { pmid: '12345678', sentence: 'HR 0.75, 95% CI 0.60-0.93', matchSpan: [0, 28] } },
                    checked: true
                }]
            }];
            renderExtractionReview();
        """)
        time.sleep(0.5)
        rp_vis = driver.execute_script("return document.getElementById('extractionReviewPanel')?.style.display")
        log_result('AE-12: Review panel visible after render', rp_vis == 'block')

        # Check evidence text is displayed
        ev = driver.execute_script("return document.querySelector('.evidence-text')?.textContent || ''")
        log_result('AE-13: Evidence text displayed', 'HR 0.75' in ev, f'evidence={ev[:80]}')

        # Check evidence highlight
        hl = driver.execute_script("return document.querySelector('.evidence-highlight')?.textContent || ''")
        log_result('AE-14: Evidence highlight present', len(hl) > 0, f'highlight={hl[:40]}')

        # Accept and verify study added
        before = driver.execute_script("return extractedStudies?.length || 0")
        driver.execute_script("acceptExtractedStudies()")
        time.sleep(0.5)
        after = driver.execute_script("return extractedStudies?.length || 0")
        log_result('AE-15: Accept adds study to extract table', after == before + 1, f'{before} -> {after}')

        # Verify source field
        src = driver.execute_script("return extractedStudies[extractedStudies.length-1]?.extractionSource || ''")
        log_result('AE-16: extractionSource set correctly', src == 'pubmed', f'source={src}')

        # Verify evidence metadata
        ev_meta = driver.execute_script("return extractedStudies[extractedStudies.length-1]?.extractionEvidence?.pubmed?.pmid || ''")
        log_result('AE-17: extractionEvidence has PMID', ev_meta == '12345678', f'pmid={ev_meta}')

        # Test smartMergeOutcomes
        print('\n=== TEST: Smart Merge ===')
        merge_result = driver.execute_script("""
            var ct = [{effectType:'HR', estimate:0.85, lowerCI:0.75, upperCI:0.96, pValue:0.01, outcomeTitle:'MACE', fieldPath:'test', arms:['Drug','Placebo']}];
            var pm = [{effectType:'HR', estimate:0.86, lowerCI:0.76, upperCI:0.97, pValue:0.01, pmid:'111', sourceSentence:'HR=0.86', matchSpan:[0,6]}];
            var merged = smartMergeOutcomes(ct, pm);
            return JSON.stringify(merged);
        """)
        mg = json.loads(merge_result)
        ct_entry = next((m for m in mg if m['source'] == 'ctgov'), None)
        both_entry = next((m for m in mg if m['source'] == 'both'), None)
        log_result('AE-18: CT.gov entry preserved in merge', ct_entry is not None and ct_entry['estimate'] == 0.85)
        log_result('AE-19: PubMed duplicate marked as "both"', both_entry is not None and both_entry['source'] == 'both')
        log_result('AE-20: Duplicate not auto-checked', both_entry is not None and not both_entry.get('checked', True))

        # Test toggle function
        print('\n=== TEST: Toggle & Export ===')
        driver.execute_script("""
            _extractionResults = [{
                nctId: 'NCT00000001', pmid: '999', title: 'Toggle Test',
                authorYear: 'Toggle 2024', doi: '', source: 'pubmed',
                outcomes: [
                    {effectType:'HR', estimate:0.5, lowerCI:0.3, upperCI:0.8, pValue:0.01, outcomeTitle:'A', source:'pubmed', evidence:{pubmed:{pmid:'999',sentence:'test',matchSpan:[0,4]}}, checked:true},
                    {effectType:'OR', estimate:1.5, lowerCI:1.1, upperCI:2.0, pValue:0.05, outcomeTitle:'B', source:'pubmed', evidence:{pubmed:{pmid:'999',sentence:'test2',matchSpan:[0,5]}}, checked:true}
                ]
            }];
            renderExtractionReview();
        """)
        time.sleep(0.3)
        # Toggle trial off
        driver.execute_script("toggleExtractionTrial(0, false)")
        c1 = driver.execute_script("return _extractionResults[0].outcomes[0].checked")
        c2 = driver.execute_script("return _extractionResults[0].outcomes[1].checked")
        log_result('AE-21: Toggle trial unchecks all outcomes', c1 == False and c2 == False)

        # Test exportEvidenceCSV exists
        has_export = driver.execute_script("return typeof exportEvidenceCSV === 'function'")
        log_result('AE-22: exportEvidenceCSV function exists', has_export)

        # Test extractFromCTGov function exists
        has_ctgov = driver.execute_script("return typeof extractFromCTGov === 'function'")
        log_result('AE-23: extractFromCTGov function exists', has_ctgov)

        # Test fetchPubMedAbstract function exists
        has_pubmed = driver.execute_script("return typeof fetchPubMedAbstract === 'function'")
        log_result('AE-24: fetchPubMedAbstract function exists', has_pubmed)

        print('\n=== TEST: Console Errors ===')
        logs = driver.get_log('browser')
        severe = [l for l in logs if l.get('level') == 'SEVERE'
                  and 'favicon' not in l.get('message', '')
                  and 'Content Security' not in l.get('message', '')
                  and 'Content-Security' not in l.get('message', '')]
        log_result('AE-25: No SEVERE console errors (excl CSP)', len(severe) == 0, f'{len(severe)} errors' + (f': {severe[0]["message"][:80]}' if severe else ''))

    except Exception as e:
        print(f'\nFATAL: {e}')
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

    total = PASS + FAIL
    print(f'\n{"="*60}')
    print(f'RESULTS: {PASS} passed, {FAIL} failed / {total} total')
    print(f'{"="*60}')
    return FAIL

if __name__ == '__main__':
    sys.exit(main())
