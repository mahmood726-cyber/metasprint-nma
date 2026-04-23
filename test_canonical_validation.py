"""Selenium tests for canonical validation panel.
Tests panel rendering, dataset embedding, and comparison logic.
WebR-dependent tests are skipped — these test UI + JS engine only."""
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
    opts.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(5)
    return d

class TestCanonicalValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        WebDriverWait(cls.driver, 30).until(EC.presence_of_element_located((By.ID, 'phase-dashboard')))
        time.sleep(1)
        try: cls.driver.execute_script("if(typeof dismissOnboarding==='function')dismissOnboarding()")
        except: pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    # Test 1: Panel exists
    def test_01_panel_exists(self):
        el = self.driver.find_element(By.ID, 'canonicalValidationSection')
        self.assertIsNotNone(el)

    # Test 2: Run button present
    def test_02_run_button(self):
        btn = self.driver.find_element(By.ID, 'canonicalRunBtn')
        # Button is inside collapsed panel so .text may be empty; use textContent
        text = btn.get_attribute('textContent') or btn.text
        self.assertIn('Run', text)

    # Test 3: Panel collapsed by default
    def test_03_collapsed_by_default(self):
        body = self.driver.find_element(By.ID, 'canonicalPanelBody')
        self.assertEqual(body.value_of_css_property('display'), 'none')

    # Test 4: Toggle works
    def test_04_toggle(self):
        self.driver.execute_script("toggleCanonicalPanel()")
        time.sleep(0.3)
        body = self.driver.find_element(By.ID, 'canonicalPanelBody')
        self.assertNotEqual(body.value_of_css_property('display'), 'none')
        self.driver.execute_script("toggleCanonicalPanel()")

    # Test 5: 5 datasets embedded
    def test_05_datasets_count(self):
        n = self.driver.execute_script("return Object.keys(NMA_VALIDATION_DATASETS).length")
        self.assertEqual(n, 5)

    # Test 6: Smoking has 24 rows
    def test_06_smoking_24_rows(self):
        n = self.driver.execute_script("return NMA_VALIDATION_DATASETS.smoking.data.length")
        self.assertEqual(n, 24)

    # Test 7: Tolerances present
    def test_07_tolerances(self):
        tol = self.driver.execute_script("return NMA_CANONICAL_TOLERANCES")
        self.assertIsNotNone(tol)
        self.assertEqual(tol['tau2_dl'], 0.001)
        self.assertEqual(tol['d'], 0.005)

    # Test 8: JS engine runs smoking dataset
    def test_08_js_runs_smoking(self):
        result = self.driver.execute_script("""
            var ds = NMA_VALIDATION_DATASETS.smoking;
            try {
                var r = _runJSonCanonicalDataset(ds);
                return { ok: true, tau2: r.dl.tau2, nT: r.dl.treatments.length };
            } catch(e) { return { ok: false, err: e.message }; }
        """)
        self.assertTrue(result['ok'], f"JS engine failed: {result.get('err')}")
        self.assertEqual(result['nT'], 4)

    # Test 9: JS engine runs all 5 datasets
    def test_09_js_runs_all(self):
        for key in ['smoking', 'oncology_hr', 'minimal', 'high_het', 'multiarm']:
            result = self.driver.execute_script(f"""
                try {{
                    var r = _runJSonCanonicalDataset(NMA_VALIDATION_DATASETS['{key}']);
                    return {{ ok: true, nT: r.dl.treatments.length }};
                }} catch(e) {{ return {{ ok: false, err: e.message }}; }}
            """)
            self.assertTrue(result['ok'], f"Dataset '{key}' failed: {result.get('err')}")

    # Test 10: Comparison function exists
    def test_10_compare_fn(self):
        exists = self.driver.execute_script("return typeof _compareCanonicalResults === 'function'")
        self.assertTrue(exists)

    # Test 11: Export function exists
    def test_11_export_fn(self):
        exists = self.driver.execute_script("return typeof exportCanonicalResults === 'function'")
        self.assertTrue(exists)

    # Test 12: ARIA attributes
    def test_12_aria(self):
        section = self.driver.find_element(By.ID, 'canonicalValidationSection')
        self.assertEqual(section.get_attribute('role'), 'region')
        self.assertIn('Cross-Validation', section.get_attribute('aria-label') or '')

    # Test 13: No severe JS errors
    def test_13_no_js_errors(self):
        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l.get('level') == 'SEVERE'
                  and 'favicon' not in l.get('message', '')
                  and 'Content Security' not in l.get('message', '')
                  and 'net::ERR' not in l.get('message', '')]
        self.assertEqual(len(severe), 0, f"{len(severe)} severe JS errors")

if __name__ == '__main__':
    print("=" * 60)
    print("CANONICAL VALIDATION — SELENIUM TESTS")
    print("=" * 60)
    unittest.main(verbosity=2)
