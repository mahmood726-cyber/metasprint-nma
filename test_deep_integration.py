"""Deep integration test: run all 5 canonical datasets through JS engine,
test comparison function, test render function."""
import io, os, sys, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metasprint-nma.html')
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')

opts = Options()
opts.add_argument('--headless=new')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=1920,1200')
opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
d = webdriver.Chrome(options=opts)
d.implicitly_wait(5)
d.get(FILE_URL)
WebDriverWait(d, 30).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
time.sleep(1)
try: d.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
except: pass

print("=" * 70)
print("DEEP INTEGRATION TEST: JS Engine on All 5 Canonical Datasets")
print("=" * 70)

datasets = ['smoking', 'oncology_hr', 'minimal', 'high_het', 'multiarm']
all_ok = True

for key in datasets:
    r = d.execute_script("""
        var ds = NMA_VALIDATION_DATASETS[arguments[0]];
        try {
            var r = _runJSonCanonicalDataset(ds);
            var dl = r.dl;
            return {
                ok: true, name: ds.name,
                nT: dl.treatments.length, treatments: dl.treatments,
                tau2: dl.tau2, I2: dl.I2global, Q: dl.Qtotal,
                hasReml: r.reml != null,
                remlTau2: r.reml ? r.reml.tau2 : null,
                hasHKSJ: r.hksj != null,
                nodesplitCount: r.nodesplit ? r.nodesplit.length : 0,
                pscores: dl.pscores ? dl.pscores.slice() : null,
                d: dl.d ? dl.d.slice() : null,
                refIdx: dl.refIdx
            };
        } catch(e) { return { ok: false, err: e.message }; }
    """, key)

    if not r['ok']:
        print(f"\n  FAIL: {key} - {r['err']}")
        all_ok = False
        continue

    print(f"\n  {key}: {r['name']}")
    print(f"    Treatments ({r['nT']}): {r['treatments']}")
    print(f"    tau2 (DL): {r['tau2']:.6f}")
    if r['remlTau2'] is not None:
        print(f"    tau2 (REML): {r['remlTau2']:.6f}")
    print(f"    I2: {r['I2']:.1f}%  Q: {r['Q']:.3f}")
    print(f"    HKSJ: {'yes' if r['hasHKSJ'] else 'no'}  Node-split: {r['nodesplitCount']} comps")

    if r['pscores']:
        print(f"    P-scores: {[round(p,3) for p in r['pscores']]}")

    if r['d']:
        ref = r['treatments'][r['refIdx']]
        effs = [f"{r['treatments'][i]}={r['d'][i]:.4f}" for i in range(r['nT']) if i != r['refIdx']]
        print(f"    Effects vs {ref}: {', '.join(effs)}")

    # Sanity
    errs = []
    if r['tau2'] < 0: errs.append('tau2<0')
    if r['I2'] < 0 or r['I2'] > 100: errs.append(f'I2={r["I2"]}')
    if r['Q'] < 0: errs.append('Q<0')
    if r['pscores']:
        for p in r['pscores']:
            if p < 0 or p > 1: errs.append(f'P={p}')
    print(f"    Sanity: {'OK' if not errs else 'ERRORS: ' + str(errs)}")
    if errs: all_ok = False

# Test comparison function
print("\n" + "=" * 70)
print("COMPARISON FUNCTION TEST (synthetic R result)")
print("=" * 70)
comp = d.execute_script("""
    var ds = NMA_VALIDATION_DATASETS.smoking;
    var js = _runJSonCanonicalDataset(ds);
    // Build fake R result in the format _compareCanonicalResults expects
    // (matches the structure from _parseRCanonicalResult)
    var t = js.dl.treatments, ri = js.dl.refIdx;
    var nonRef = [];
    for (var i = 0; i < t.length; i++) { if (i !== ri) nonRef.push(t[i]); }
    var effs = [], ses = [], pscores = [];
    for (var i = 0; i < t.length; i++) {
        pscores.push(js.dl.pscores[i] + 0.005);
        if (i === ri) continue;
        effs.push(js.dl.d[i] + 0.001);
        var vii = js.dl.V[i][i], vrr = js.dl.V[ri][ri], vir = js.dl.V[i][ri];
        ses.push(Math.sqrt(Math.max(0, vii + vrr - 2*vir)) + 0.001);
    }
    var rr = {
        tau2_dl: js.dl.tau2 + 0.0001,
        tau2_reml: js.reml ? js.reml.tau2 + 0.001 : null,
        I2: js.dl.I2global + 0.5,
        Q: js.dl.Qtotal + 0.1,
        treatments: t, nonRefTreats: nonRef,
        effects_dl: effs, ses_dl: ses, pscores: pscores
    };
    var c = _compareCanonicalResults(js, rr, ds, NMA_CANONICAL_TOLERANCES);
    var p = c.filter(function(x){return x.pass===true}).length;
    var f = c.filter(function(x){return x.pass===false}).length;
    var s = c.filter(function(x){return x.pass===null}).length;
    return {total: c.length, passed: p, failed: f, skipped: s};
""")
print(f"  {comp['total']} checks: {comp['passed']} PASS, {comp['failed']} FAIL, {comp['skipped']} SKIP")

# Test render function
print("\n" + "=" * 70)
print("RENDER FUNCTION TEST")
print("=" * 70)
rend = d.execute_script("""
    var ds=NMA_VALIDATION_DATASETS.minimal;
    var js=_runJSonCanonicalDataset(ds);
    var t=js.dl.treatments, ri=js.dl.refIdx;
    var nonRef=[];
    for(var i=0;i<t.length;i++){if(i!==ri)nonRef.push(t[i]);}
    var effs=[],ses=[],pscores=[];
    for(var i=0;i<t.length;i++){
        pscores.push(js.dl.pscores[i]);
        if(i===ri)continue;
        effs.push(js.dl.d[i]);
        var vii=js.dl.V[i][i],vrr=js.dl.V[ri][ri],vir=js.dl.V[i][ri];
        ses.push(Math.sqrt(Math.max(0,vii+vrr-2*vir)));
    }
    var rr={tau2_dl:js.dl.tau2, tau2_reml:js.reml?js.reml.tau2:null,
            I2:js.dl.I2global, Q:js.dl.Qtotal,
            treatments:t, nonRefTreats:nonRef,
            effects_dl:effs, ses_dl:ses, pscores:pscores};
    var c=_compareCanonicalResults(js,rr,ds,NMA_CANONICAL_TOLERANCES);
    var ar={minimal:{checks:c,passed:c.length,failed:0,skipped:0}};
    var el=document.createElement('div');
    _renderCanonicalResults(ar,c.length,0,0,'test',true,el);
    return {len:el.innerHTML.length, valid:el.innerHTML.indexOf('VALIDATED')>=0, table:el.innerHTML.indexOf('<table')>=0};
""")
print(f"  HTML: {rend['len']} chars, VALIDATED={rend['valid']}, table={rend['table']}")

# Console errors
logs = d.get_log('browser')
severe = [l for l in logs if l.get('level')=='SEVERE' and 'favicon' not in l.get('message','') and 'net::ERR' not in l.get('message','')]
print(f"\n  Console: {len(severe)} severe, {len(logs)} total")

print("\n" + "=" * 70)
print(f"OVERALL: {'ALL PASS' if all_ok and not severe else 'ISSUES FOUND'}")
print("=" * 70)
d.quit()
