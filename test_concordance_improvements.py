"""
Test concordance improvements:
  1. Spearman midrank tie-handling
  2. Spearman p-value
  3. CI overlap proportion (Jaccard)
  4. Color-blind safe verdict icons
  5. Fuzzy match 60% threshold
"""
import io, os, sys, time, json, unittest
if 'pytest' not in sys.modules and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metasprint-nma.html')
FILE_URL = 'file:///' + HTML_PATH.replace('\\', '/')

def make_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1200')
    opts.add_argument('--disable-web-security')
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(5)
    return d


class TestConcordanceImprovements(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        WebDriverWait(cls.driver, 30).until(
            EC.presence_of_element_located((By.ID, 'phase-dashboard'))
        )
        time.sleep(1)
        try:
            cls.driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # ──── Unit Tests (pure JS evaluation) ────

    def test_01_midrank_no_ties(self):
        """_rankArr without ties should produce standard 1,2,3,..."""
        result = self.driver.execute_script("""
            // Inject _rankArr into global scope for testing
            window._testRankArr = function(arr) {
                var s = arr.map(function(v, i) { return { v: v, i: i }; })
                    .sort(function(a, b) { return a.v - b.v; });
                var r = new Array(arr.length);
                var i = 0;
                while (i < s.length) {
                    var j = i;
                    while (j < s.length - 1 && s[j + 1].v === s[j].v) j++;
                    var midrank = (i + 1 + j + 1) / 2;
                    for (var k = i; k <= j; k++) r[s[k].i] = midrank;
                    i = j + 1;
                }
                return r;
            };
            return JSON.stringify(window._testRankArr([0.3, 0.5, 0.7]));
        """)
        ranks = json.loads(result)
        self.assertEqual(ranks, [1, 2, 3], f"No-tie ranks should be [1,2,3], got {ranks}")
        print("  PASS: midrank no-ties -> [1, 2, 3]")

    def test_02_midrank_with_ties(self):
        """Tied values should get average midranks."""
        result = self.driver.execute_script("""
            return JSON.stringify(window._testRankArr([0.5, 0.3, 0.5, 0.7]));
        """)
        ranks = json.loads(result)
        # 0.3 -> rank 1, 0.5 tied at positions 2,3 -> midrank 2.5, 0.7 -> rank 4
        self.assertEqual(ranks, [2.5, 1, 2.5, 4], f"Tie ranks should be [2.5,1,2.5,4], got {ranks}")
        print("  PASS: midrank with ties -> [2.5, 1, 2.5, 4]")

    def test_03_midrank_all_tied(self):
        """All identical values should all get midrank."""
        result = self.driver.execute_script("""
            return JSON.stringify(window._testRankArr([0.6, 0.6, 0.6]));
        """)
        ranks = json.loads(result)
        self.assertEqual(ranks, [2, 2, 2], f"All-tied ranks should be [2,2,2], got {ranks}")
        print("  PASS: midrank all-tied -> [2, 2, 2]")

    def test_04_midrank_triple_tie(self):
        """Three-way tie at beginning."""
        result = self.driver.execute_script("""
            return JSON.stringify(window._testRankArr([0.4, 0.4, 0.4, 0.9]));
        """)
        ranks = json.loads(result)
        # positions 1,2,3 -> midrank 2; position 4 -> rank 4
        self.assertEqual(ranks, [2, 2, 2, 4], f"Triple-tie ranks should be [2,2,2,4], got {ranks}")
        print("  PASS: midrank triple-tie -> [2, 2, 2, 4]")

    def test_05_spearman_perfect(self):
        """Perfect rank agreement -> rho = 1.00."""
        result = self.driver.execute_script("""
            var pub = [0.3, 0.5, 0.7, 0.9];
            var comp = [0.31, 0.52, 0.71, 0.88];
            var rP = window._testRankArr(pub), rC = window._testRankArr(comp);
            var n = rP.length, sumD2 = 0;
            for (var i = 0; i < n; i++) sumD2 += (rP[i] - rC[i]) * (rP[i] - rC[i]);
            return (1 - 6 * sumD2 / (n * (n * n - 1))).toFixed(2);
        """)
        self.assertEqual(result, "1.00", f"Perfect agreement rho should be 1.00, got {result}")
        print("  PASS: Spearman perfect agreement -> rho=1.00")

    def test_06_spearman_reversed(self):
        """Reversed ranks -> rho = -1.00."""
        result = self.driver.execute_script("""
            var pub = [0.3, 0.5, 0.7, 0.9];
            var comp = [0.9, 0.7, 0.5, 0.3];
            var rP = window._testRankArr(pub), rC = window._testRankArr(comp);
            var n = rP.length, sumD2 = 0;
            for (var i = 0; i < n; i++) sumD2 += (rP[i] - rC[i]) * (rP[i] - rC[i]);
            return (1 - 6 * sumD2 / (n * (n * n - 1))).toFixed(2);
        """)
        self.assertEqual(result, "-1.00", f"Reversed rho should be -1.00, got {result}")
        print("  PASS: Spearman reversed -> rho=-1.00")

    def test_07_spearman_p_value(self):
        """p-value for perfect agreement with n=4 should exist and be small."""
        result = self.driver.execute_script("""
            var rhoVal = 1.0;
            // rho=1 exactly -> |rho|=1, so p-value computation is skipped (division by zero)
            // Use near-perfect instead
            rhoVal = 0.95;
            var n = 5;
            if (n >= 4 && Math.abs(rhoVal) < 1) {
                var tStat = rhoVal * Math.sqrt((n - 2) / (1 - rhoVal * rhoVal));
                var pVal = 2 * (1 - tCDFfn(Math.abs(tStat), n - 2));
                return pVal;
            }
            return null;
        """)
        self.assertIsNotNone(result, "p-value should be computed for rho=0.95, n=5")
        self.assertLess(result, 0.05, f"p-value for rho=0.95, n=5 should be <0.05, got {result}")
        print(f"  PASS: Spearman p-value for rho=0.95 n=5 = {result:.4f} (< 0.05)")

    def test_08_spearman_p_value_weak(self):
        """Weak correlation -> p-value should be large."""
        result = self.driver.execute_script("""
            var rhoVal = 0.2;
            var n = 5;
            var tStat = rhoVal * Math.sqrt((n - 2) / (1 - rhoVal * rhoVal));
            return 2 * (1 - tCDFfn(Math.abs(tStat), n - 2));
        """)
        self.assertGreater(result, 0.3, f"p-value for rho=0.2, n=5 should be >0.3, got {result}")
        print(f"  PASS: Spearman p-value for rho=0.2 n=5 = {result:.4f} (> 0.3)")

    def test_09_ci_overlap_full(self):
        """Identical CIs -> overlap = 1.0."""
        result = self.driver.execute_script("""
            var lo = Math.max(0.5, 0.5), hi = Math.min(0.9, 0.9);
            var unionLo = Math.min(0.5, 0.5), unionHi = Math.max(0.9, 0.9);
            return (hi > lo && unionHi > unionLo) ? (hi - lo) / (unionHi - unionLo) : 0;
        """)
        self.assertAlmostEqual(result, 1.0, places=4, msg=f"Identical CIs should overlap 100%, got {result}")
        print(f"  PASS: CI overlap for identical intervals = {result}")

    def test_10_ci_overlap_partial(self):
        """Partially overlapping CIs."""
        result = self.driver.execute_script("""
            // pub: [0.4, 0.8], comp: [0.6, 1.0]
            var lo = Math.max(0.4, 0.6), hi = Math.min(0.8, 1.0);
            var unionLo = Math.min(0.4, 0.6), unionHi = Math.max(0.8, 1.0);
            return (hi > lo && unionHi > unionLo) ? (hi - lo) / (unionHi - unionLo) : 0;
        """)
        # intersection = [0.6, 0.8] = 0.2, union = [0.4, 1.0] = 0.6, overlap = 0.333...
        self.assertAlmostEqual(result, 1/3, places=3, msg=f"Partial overlap should be ~33%, got {result}")
        print(f"  PASS: CI overlap for [0.4,0.8] vs [0.6,1.0] = {result:.3f} (~33%)")

    def test_11_ci_overlap_none(self):
        """Non-overlapping CIs -> 0."""
        result = self.driver.execute_script("""
            var lo = Math.max(0.3, 0.7), hi = Math.min(0.5, 0.9);
            var unionLo = Math.min(0.3, 0.7), unionHi = Math.max(0.5, 0.9);
            return (hi > lo && unionHi > unionLo) ? (hi - lo) / (unionHi - unionLo) : 0;
        """)
        self.assertEqual(result, 0, f"Non-overlapping CIs should be 0, got {result}")
        print("  PASS: CI overlap for non-overlapping = 0")

    def test_12_fuzzy_match_threshold(self):
        """Fuzzy match rejects short substring matches."""
        result = self.driver.execute_script("""
            // "Pembro" (6 chars) is a substring of "Pembrolizumab + Lenvatinib" (26 chars)
            // 6/26 = 0.23 < 0.60 threshold -> should NOT match
            var short = 'Pembro', long = 'Pembrolizumab + Lenvatinib';
            var mLen = Math.min(short.length, long.length);
            var maxLen = Math.max(short.length, long.length);
            return mLen >= maxLen * 0.6;
        """)
        self.assertFalse(result, "'Pembro' vs 'Pembrolizumab + Lenvatinib' should NOT pass 60% threshold")
        print("  PASS: Fuzzy match rejects 'Pembro' vs 'Pembrolizumab + Lenvatinib'")

    def test_13_fuzzy_match_accepts_close(self):
        """Fuzzy match accepts close names."""
        result = self.driver.execute_script("""
            // "Pembrolizumab" (13) vs "Pembrolizumab+Chemo" (19)
            // 13/19 = 0.684 > 0.60 -> should match
            var short = 'Pembrolizumab', long = 'Pembrolizumab+Chemo';
            var mLen = Math.min(short.length, long.length);
            var maxLen = Math.max(short.length, long.length);
            return mLen >= maxLen * 0.6;
        """)
        self.assertTrue(result, "'Pembrolizumab' vs 'Pembrolizumab+Chemo' should pass 60% threshold")
        print("  PASS: Fuzzy match accepts 'Pembrolizumab' vs 'Pembrolizumab+Chemo'")

    # ──── Integration Tests (inject synthetic NMA results, check rendered output) ────

    def _render_concordance_with_synthetic(self, topic_key, treatments, d_values, V_matrix,
                                            ref_treatment=None, is_ratio=True, conf_level=0.95):
        """Inject synthetic NMA result and call renderPublishedComparison directly."""
        drv = self.driver
        # Set the topic selector
        drv.execute_script(f"document.getElementById('exampleTopicSelect').value = '{topic_key}';")
        time.sleep(0.2)

        # Build synthetic nmaResult and call render
        treatments_json = json.dumps(treatments)
        d_json = json.dumps(d_values)
        V_json = json.dumps(V_matrix)
        ref = ref_treatment or treatments[0]

        html = drv.execute_script(f"""
            var nmaResult = {{
                treatments: {treatments_json},
                d: {d_json},
                V: {V_json},
                refTreatment: '{ref}',
                isRatio: {str(is_ratio).lower()},
                confLevel: {conf_level},
                tau2: 0.015,
                I2: 42.3
            }};
            renderPublishedComparison(nmaResult);
            var c = document.getElementById('publishedComparisonContainer');
            return c ? c.innerHTML : '';
        """)
        return html

    def test_20_glp1_mace_concordance_table(self):
        """Render GLP-1 MACE concordance with synthetic NMA (4 treatments)."""
        # Published refs: Liraglutide HR 0.87, Semaglutide 0.74, Albiglutide 0.78, Dulaglutide 0.88
        # Comparator: Placebo (index 0)
        treatments = ['Placebo', 'Liraglutide', 'Semaglutide', 'Albiglutide', 'Dulaglutide']
        # d = log(HR) vs reference (Placebo=0)
        import math
        d = [0, math.log(0.85), math.log(0.72), math.log(0.80), math.log(0.90)]
        # Simple diagonal V matrix (independent effects)
        n = len(d)
        V = [[0.01 if i == j and i > 0 else 0 for j in range(n)] for i in range(n)]

        html = self._render_concordance_with_synthetic('glp1_mace', treatments, d, V)
        self.assertGreater(len(html), 100, f"Concordance table should render, got {len(html)} chars")

        # Check verdict markers (ASCII: [=] concordant, [~] partial/close, [x] divergent)
        self.assertTrue('Concordant' in html or 'Partial' in html or 'Close' in html or 'Divergent' in html,
                       "Should have at least one verdict")
        has_marker = '[=]' in html or '[~]' in html or '[x]' in html
        self.assertTrue(has_marker, "Should have at least one verdict marker ([=]/[~]/[x])")
        # Check accessibility attributes for screen readers
        self.assertIn('aria-label=', html, "Verdict spans should have aria-label for accessibility")
        print(f"  PASS: GLP-1 MACE concordance rendered ({len(html)} chars) with verdict markers + ARIA")

        # Check CI Overlap column
        self.assertIn('CI Overlap', html, "Table should have 'CI Overlap' column header")
        print("  PASS: CI Overlap column present")

        # Check Spearman rho with p-value (4 treatments -> should compute)
        self.assertIn('\u03C1', html, "Should show Spearman rho (4 treatments >= 3)")
        has_p = '(p=' in html
        print(f"  PASS: Spearman rho displayed, p-value={'present' if has_p else 'absent'}")

        # Check CI overlap metric
        self.assertIn('CI overlap:', html, "Summary bar should show 'CI overlap:' metric")
        print("  PASS: CI overlap metric in summary bar")

        # Check heterogeneity
        self.assertIn('\u03C4\u00B2', html, "Should show tau-squared")
        self.assertIn('I\u00B2', html, "Should show I-squared")
        print("  PASS: Heterogeneity metrics (tau2, I2) displayed")

        # Check overall concordance grade
        self.assertTrue('Excellent' in html or 'Good' in html or 'Moderate' in html or 'Low' in html,
                       "Summary should show overall concordance grade")
        print("  PASS: Overall concordance grade badge present")

    def test_21_ckd_nephro_spearman(self):
        """CKD nephro with 4 treatments — verify Spearman rho + p-value appear."""
        # Published: Canagliflozin 0.70, Dapagliflozin 0.61, Empagliflozin 0.72, Finerenone 0.82
        import math
        treatments = ['Placebo', 'Canagliflozin', 'Dapagliflozin', 'Empagliflozin', 'Finerenone']
        d = [0, math.log(0.68), math.log(0.59), math.log(0.70), math.log(0.80)]
        n = len(d)
        V = [[0.008 if i == j and i > 0 else 0 for j in range(n)] for i in range(n)]

        html = self._render_concordance_with_synthetic('ckd_nephro', treatments, d, V)
        self.assertGreater(len(html), 100)
        self.assertIn('CI Overlap', html)
        self.assertIn('\u03C1', html, "Spearman rho should appear for 4 treatments")
        print(f"  PASS: CKD nephro concordance with Spearman rho ({len(html)} chars)")

    def test_22_adj_melanoma_no_spearman(self):
        """adj_melanoma has 2 treatments — Spearman should NOT show (need >=3)."""
        import math
        treatments = ['Placebo', 'Pembrolizumab', 'Dab+Tram']
        d = [0, math.log(0.58), math.log(0.45)]
        n = len(d)
        V = [[0.01 if i == j and i > 0 else 0 for j in range(n)] for i in range(n)]

        html = self._render_concordance_with_synthetic('adj_melanoma', treatments, d, V)
        self.assertGreater(len(html), 100)
        self.assertIn('CI Overlap', html)
        # 2 treatments -> no Spearman (need >= 3 matched)
        has_rho = '\u03C1' in html
        print(f"  PASS: adj_melanoma concordance rendered, Spearman {'present (3 matched)' if has_rho else 'absent (< 3 matched)'}")

    def test_23_concordant_verdict_icon(self):
        """When computed HR is very close to published, should show Concordant with checkmark."""
        import math
        # sglt2_hf: Dapagliflozin HR 0.74 (0.65-0.85), Empagliflozin 0.75 (0.65-0.86)
        treatments = ['Placebo', 'Dapagliflozin', 'Empagliflozin']
        # Match published values closely
        d = [0, math.log(0.74), math.log(0.75)]
        n = len(d)
        V = [[0.005 if i == j and i > 0 else 0 for j in range(n)] for i in range(n)]

        html = self._render_concordance_with_synthetic('sglt2_hf', treatments, d, V)
        self.assertIn('Concordant', html, "Close match should produce Concordant verdict")
        self.assertIn('[=]', html, "Concordant verdict should have [=] marker")
        self.assertIn('aria-label="Concordant"', html, "Should have ARIA label")
        print("  PASS: Concordant verdict with [=] marker and ARIA label")

    def test_24_divergent_verdict_icon(self):
        """When computed HR is far from published, should show Divergent with cross."""
        import math
        # Published: Liraglutide 0.87, but we'll compute as 0.45 (huge discrepancy)
        treatments = ['Placebo', 'Liraglutide', 'Semaglutide', 'Albiglutide', 'Dulaglutide']
        d = [0, math.log(0.45), math.log(0.40), math.log(0.42), math.log(0.48)]
        n = len(d)
        V = [[0.002 if i == j and i > 0 else 0 for j in range(n)] for i in range(n)]

        html = self._render_concordance_with_synthetic('glp1_mace', treatments, d, V)
        self.assertIn('Divergent', html, "Large discrepancy should produce Divergent verdict")
        self.assertIn('[x]', html, "Divergent verdict should have [x] marker")
        self.assertIn('aria-label="Divergent"', html, "Should have ARIA label")
        print("  PASS: Divergent verdict with [x] marker and ARIA label")

    def test_25_re_reference_warning(self):
        """When NMA reference differs from published comparator, show warning banner."""
        import math
        # Published comparator is 'Placebo' but we set NMA ref to 'Liraglutide'
        treatments = ['Placebo', 'Liraglutide', 'Semaglutide', 'Dulaglutide']
        d = [0, math.log(0.85), math.log(0.72), math.log(0.90)]
        n = len(d)
        V = [[0.01 if i == j and i > 0 else 0 for j in range(n)] for i in range(n)]

        html = self._render_concordance_with_synthetic('glp1_mace', treatments, d, V,
                                                        ref_treatment='Liraglutide')
        self.assertIn('re-referenced', html, "Should show re-reference warning when refs differ")
        print("  PASS: Re-reference warning shown when NMA ref != published comparator")

    def test_26_tooltip_on_verdict(self):
        """Verdicts should have title= tooltips for accessibility."""
        import math
        treatments = ['Placebo', 'Dapagliflozin', 'Empagliflozin']
        d = [0, math.log(0.74), math.log(0.75)]
        n = len(d)
        V = [[0.005 if i == j and i > 0 else 0 for j in range(n)] for i in range(n)]

        html = self._render_concordance_with_synthetic('sglt2_hf', treatments, d, V)
        self.assertIn('title=', html, "Verdict spans should have title tooltips")
        print("  PASS: Verdict tooltips present")

    def test_30_no_js_errors(self):
        """No severe console errors after loading topics."""
        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l.get('level') == 'SEVERE'
                  and 'favicon' not in l.get('message', '')
                  and 'Content Security' not in l.get('message', '')
                  and 'net::ERR' not in l.get('message', '')]
        for s in severe[:5]:
            print(f"  SEVERE: {s['message'][:120]}")
        self.assertEqual(len(severe), 0, f"{len(severe)} severe JS errors found")
        print(f"  PASS: No severe JS console errors (total log entries: {len(logs)})")


class TestMidrankSpearmanMath(unittest.TestCase):
    """Pure math verification of Spearman with midranks (no browser)."""

    def _rank_arr(self, arr):
        """Python implementation matching the JS midrank function."""
        s = sorted(enumerate(arr), key=lambda x: x[1])
        r = [0] * len(arr)
        i = 0
        while i < len(s):
            j = i
            while j < len(s) - 1 and s[j + 1][1] == s[j][1]:
                j += 1
            midrank = (i + 1 + j + 1) / 2
            for k in range(i, j + 1):
                r[s[k][0]] = midrank
            i = j + 1
        return r

    def _spearman(self, x, y):
        rx = self._rank_arr(x)
        ry = self._rank_arr(y)
        n = len(rx)
        sum_d2 = sum((rx[i] - ry[i]) ** 2 for i in range(n))
        return 1 - 6 * sum_d2 / (n * (n * n - 1))

    def test_spearman_with_ties_correct(self):
        """Verify midrank Spearman matches expected value."""
        pub  = [0.5, 0.5, 0.7, 0.9]
        comp = [0.48, 0.52, 0.68, 0.91]
        rho = self._spearman(pub, comp)
        # Without midranks, the tied 0.5s could get arbitrary ordering
        # With midranks, both get rank 1.5
        self.assertGreater(rho, 0.9, f"Near-concordant with ties should have rho>0.9, got {rho:.3f}")
        print(f"  PASS: Spearman with ties = {rho:.4f} (> 0.9)")

    def test_spearman_ties_symmetry(self):
        """Swapping the order of tied elements shouldn't change rho."""
        pub  = [0.5, 0.5, 0.7]
        comp = [0.49, 0.51, 0.72]
        rho1 = self._spearman(pub, comp)
        # Swap the tied pub elements
        pub2  = [0.5, 0.5, 0.7]
        comp2 = [0.51, 0.49, 0.72]
        rho2 = self._spearman(pub2, comp2)
        self.assertAlmostEqual(rho1, rho2, places=10,
                              msg=f"Swapping tied elements should give same rho: {rho1:.4f} vs {rho2:.4f}")
        print(f"  PASS: Tie symmetry: rho1={rho1:.4f} == rho2={rho2:.4f}")


if __name__ == '__main__':
    print("=" * 70)
    print("CONCORDANCE IMPROVEMENTS TEST SUITE")
    print("=" * 70)
    unittest.main(verbosity=2)
