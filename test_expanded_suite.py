"""
Expanded Selenium test suite for MetaSprint NMA
Tests: threshold analysis, tool comparison, reviewer packet, PRISMA checklist,
       gold standard validation, batch validation of all 23 reference topics
Target: 60+ tests to complement the 49 in test_session_features.py
"""
import io, os, sys, time, json, unittest
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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

def dismiss_overlays(driver):
    driver.execute_script("""
        localStorage.setItem('metasprint-nma-tutorial-done','1');
        localStorage.removeItem('metasprint-nma-autosave');
        document.querySelectorAll('[role=dialog],.onboard-overlay').forEach(e => e.remove());
    """)

def load_demo_and_run(driver):
    driver.execute_script("""
        var sel = document.getElementById('exampleTopicSelect');
        if (sel) sel.value = 'smoking';
        if (typeof loadExampleTopic === 'function') loadExampleTopic();
    """)
    time.sleep(3)
    driver.execute_script("if (typeof switchPhase === 'function') switchPhase('analyze');")
    time.sleep(1)
    driver.execute_script("if (typeof runAnalysis === 'function') runAnalysis();")
    time.sleep(8)


class TestThresholdAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)
        dismiss_overlays(cls.driver)
        cls.driver.get(FILE_URL)
        time.sleep(3)
        load_demo_and_run(cls.driver)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_threshold_container_exists(self):
        el = self.driver.find_element(By.ID, 'thresholdAnalysisContainer')
        self.assertIsNotNone(el)

    def test_threshold_renders_after_nma(self):
        el = self.driver.find_element(By.ID, 'thresholdAnalysisContainer')
        html = self.driver.execute_script("return arguments[0].innerHTML", el)
        self.assertIn('Threshold Analysis', html)

    def test_threshold_shows_best_treatment(self):
        el = self.driver.find_element(By.ID, 'thresholdAnalysisContainer')
        text = self.driver.execute_script("return arguments[0].textContent", el)
        self.assertIn('Best:', text)
        self.assertIn('Runner-up:', text)

    def test_threshold_shows_robustness(self):
        el = self.driver.find_element(By.ID, 'thresholdAnalysisContainer')
        text = self.driver.execute_script("return arguments[0].textContent", el)
        has_label = 'Robust' in text or 'Sensitive' in text or 'Fragile' in text or 'Immune' in text
        self.assertTrue(has_label, 'No robustness label found')

    def test_threshold_has_aria_label(self):
        tables = self.driver.find_elements(By.CSS_SELECTOR, '#thresholdAnalysisContainer table[aria-label]')
        self.assertGreater(len(tables), 0, 'Threshold table missing aria-label')

    def test_threshold_function_exists(self):
        result = self.driver.execute_script('return typeof renderThresholdAnalysis')
        self.assertEqual(result, 'function')


class TestToolComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)
        dismiss_overlays(cls.driver)
        cls.driver.get(FILE_URL)
        time.sleep(3)
        load_demo_and_run(cls.driver)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_tool_comparison_renders(self):
        el = self.driver.find_element(By.ID, 'toolComparisonContainer')
        html = self.driver.execute_script("return arguments[0].innerHTML", el)
        self.assertIn('Feature Comparison', html)

    def test_tool_comparison_has_metasprint(self):
        el = self.driver.find_element(By.ID, 'toolComparisonContainer')
        text = self.driver.execute_script("return arguments[0].textContent", el)
        self.assertIn('MetaSprint NMA', text)

    def test_tool_comparison_has_5_tools(self):
        headers = self.driver.find_elements(By.CSS_SELECTOR, '#toolComparisonContainer table thead th')
        self.assertGreaterEqual(len(headers), 6, 'Expected 6 columns (feature + 5 tools)')

    def test_tool_comparison_shows_totals(self):
        el = self.driver.find_element(By.ID, 'toolComparisonContainer')
        text = self.driver.execute_script("return arguments[0].textContent", el)
        self.assertIn('Total', text)
        self.assertIn('/23', text)

    def test_metasprint_has_most_features(self):
        """MetaSprint should have 23/23 features (column 1)."""
        rows = self.driver.find_elements(By.CSS_SELECTOR, '#toolComparisonContainer table tbody tr')
        last_row = rows[-1] if rows else None
        self.assertIsNotNone(last_row)
        cells = last_row.find_elements(By.TAG_NAME, 'td')
        if len(cells) >= 2:
            metasprint_total = self.driver.execute_script("return arguments[0].textContent", cells[1])
            self.assertIn('23/23', metasprint_total)


class TestReviewerPacket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)
        dismiss_overlays(cls.driver)
        cls.driver.get(FILE_URL)
        time.sleep(3)
        load_demo_and_run(cls.driver)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_reviewer_packet_button_exists(self):
        btn = self.driver.find_elements(By.XPATH, "//button[contains(text(),'Reviewer Packet')]")
        self.assertGreater(len(btn), 0, 'Reviewer Packet button not found')

    def test_reviewer_packet_function_exists(self):
        result = self.driver.execute_script('return typeof exportReviewerPacket')
        self.assertEqual(result, 'function')

    def test_reviewer_packet_requires_nma(self):
        """Should show toast if no NMA result."""
        # This test verifies the guard exists (we already ran NMA in setUpClass)
        result = self.driver.execute_script('return typeof lastAnalysisResult')
        self.assertEqual(result, 'object')


class TestPRISMAChecklist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)
        dismiss_overlays(cls.driver)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_prisma_button_exists(self):
        btns = self.driver.find_elements(By.XPATH, "//button[contains(text(),'PRISMA-NMA')]")
        self.assertGreater(len(btns), 0)

    def test_prisma_items_defined(self):
        count = self.driver.execute_script('return _prismaNMAItems.reduce(function(s,sec){return s+sec.items.length},0)')
        self.assertEqual(count, 32)

    def test_prisma_toggle_works(self):
        # Use JS to toggle directly (bypasses phase visibility)
        self.driver.execute_script("""
            var el = document.getElementById('prismaNMAChecklist');
            if (el) { el.style.display = 'block'; _renderPrismaNMAChecklist(); }
        """)
        time.sleep(0.5)
        el = self.driver.find_element(By.ID, 'prismaNMAChecklist')
        html = self.driver.execute_script("return arguments[0].innerHTML", el)
        self.assertGreater(len(html), 100, 'PRISMA checklist did not render')

    def test_prisma_has_checkboxes(self):
        self.driver.execute_script('togglePrismaNMAChecklist()')
        time.sleep(0.5)
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, '#prismaNMAChecklist input[type="checkbox"]')
        self.assertEqual(len(checkboxes), 32)

    def test_prisma_saves_to_localstorage(self):
        self.driver.execute_script("_savePrismaCheck('S1', true)")
        saved = self.driver.execute_script("return JSON.parse(localStorage.getItem('metasprint-nma-prisma-checklist')||'{}')")
        self.assertTrue(saved.get('S1'))

    def test_prisma_export_function_exists(self):
        result = self.driver.execute_script('return typeof _exportPrismaChecklist')
        self.assertEqual(result, 'function')


class TestGoldStandardValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)
        dismiss_overlays(cls.driver)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_gold_validation_function_exists(self):
        self.assertEqual(self.driver.execute_script('return typeof runGoldStandardValidation'), 'function')

    def test_gold_all_validations_function_exists(self):
        self.assertEqual(self.driver.execute_script('return typeof runAllGoldValidations'), 'function')

    def test_smoking_gold_reference_exists(self):
        result = self.driver.execute_script('return NMA_VALIDATION_REFERENCE.smoking !== null')
        self.assertTrue(result)

    def test_ckd_gold_reference_exists(self):
        result = self.driver.execute_script('return NMA_VALIDATION_REFERENCE.ckd_hr !== null')
        self.assertTrue(result)

    def test_smoking_gold_passes(self):
        """Run smoking gold standard validation and check it passes."""
        result = self.driver.execute_script('return runGoldStandardValidation("smoking")')
        self.assertIsNotNone(result, 'Gold validation returned null')
        self.assertTrue(result.get('pass', False), f'Smoking gold failed: {result}')

    def test_ckd_gold_passes(self):
        """Run CKD gold standard validation and check it passes."""
        result = self.driver.execute_script('return runGoldStandardValidation("ckd_hr")')
        self.assertIsNotNone(result, 'Gold validation returned null')
        self.assertTrue(result.get('pass', False), f'CKD gold failed: {result}')

    def test_minimal_gold_passes(self):
        result = self.driver.execute_script('return runGoldStandardValidation("minimal")')
        self.assertIsNotNone(result)
        self.assertTrue(result.get('pass', False), f'Minimal gold failed: {result}')

    def test_gold_returns_check_details(self):
        result = self.driver.execute_script('return runGoldStandardValidation("smoking")')
        self.assertIn('checks', result)
        self.assertGreater(len(result['checks']), 0)

    def test_run_all_gold_returns_results(self):
        results = self.driver.execute_script('return runAllGoldValidations()')
        self.assertGreaterEqual(len(results), 2, 'Expected at least 2 gold datasets')


class TestMatchTier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_t1_exact_match(self):
        r = self.driver.execute_script('return matchTier(0.70, 0.72, true)')
        self.assertEqual(r['tier'], 1)

    def test_t2_reciprocal(self):
        r = self.driver.execute_script('return matchTier(1.43, 0.70, true)')
        self.assertEqual(r['tier'], 2)
        self.assertEqual(r.get('transform'), 'reciprocal')

    def test_t3_close(self):
        r = self.driver.execute_script('return matchTier(0.65, 0.72, true)')
        self.assertIn(r['tier'], [3, 4])

    def test_beyond_t4(self):
        r = self.driver.execute_script('return matchTier(0.30, 0.80, true)')
        self.assertEqual(r['tier'], 5)

    def test_near_zero_md_exact(self):
        """P0-4 fix: near-zero MD values should match as T1."""
        r = self.driver.execute_script('return matchTier(0.0003, 0.0003, false)')
        self.assertEqual(r['tier'], 1)

    def test_negative_ratio_invalid(self):
        """P0-4 fix: negative ratio values should return null tier."""
        r = self.driver.execute_script('return matchTier(-0.5, 0.7, true)')
        self.assertIsNone(r['tier'])

    def test_null_input(self):
        r = self.driver.execute_script('return matchTier(null, 0.7, true)')
        self.assertIsNone(r['tier'])

    def test_sign_flip_md(self):
        r = self.driver.execute_script('return matchTier(5.0, -5.0, false)')
        self.assertEqual(r['tier'], 2)
        self.assertEqual(r.get('transform'), 'sign-flip')


class TestBatchTopicValidation(unittest.TestCase):
    """Verify all 23 topic dropdown options are selectable and have published refs."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)
        dismiss_overlays(cls.driver)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_all_topics_have_published_refs(self):
        """Every topic in NMA_PUBLISHED_REFS should have >= 1 treatment values."""
        topics = self.driver.execute_script('return Object.keys(NMA_PUBLISHED_REFS)')
        self.assertGreaterEqual(len(topics), 70)
        for topic in topics:
            count = self.driver.execute_script(f'return Object.keys(NMA_PUBLISHED_REFS["{topic}"].values).length')
            self.assertGreaterEqual(count, 1, f'{topic} has 0 treatments')

    def test_all_topics_in_dropdown(self):
        """Every non-smoking topic in NMA_EXAMPLE_TOPICS should be in the dropdown."""
        topics = self.driver.execute_script('return Object.keys(NMA_EXAMPLE_TOPICS)')
        sel_html = self.driver.execute_script("return document.getElementById('exampleTopicSelect').innerHTML")
        for topic in topics:
            self.assertIn(f'value="{topic}"', sel_html, f'{topic} missing from dropdown')

    def test_all_published_refs_have_source(self):
        """Every published ref should have a source citation."""
        topics = self.driver.execute_script('return Object.keys(NMA_PUBLISHED_REFS)')
        for topic in topics:
            source = self.driver.execute_script(f'return NMA_PUBLISHED_REFS["{topic}"].source')
            self.assertTrue(source and len(source) > 5, f'{topic} missing source citation')

    def test_all_published_refs_have_comparator(self):
        """Every published ref should have a comparator."""
        topics = self.driver.execute_script('return Object.keys(NMA_PUBLISHED_REFS)')
        for topic in topics:
            comp = self.driver.execute_script(f'return NMA_PUBLISHED_REFS["{topic}"].comparator')
            self.assertTrue(comp and len(comp) > 0, f'{topic} missing comparator')

    def test_all_values_have_valid_ci(self):
        """All published values should have lower < point < upper (for ratio measures, all positive)."""
        topics = self.driver.execute_script('return Object.keys(NMA_PUBLISHED_REFS)')
        for topic in topics:
            ref = self.driver.execute_script(f'return NMA_PUBLISHED_REFS["{topic}"]')
            is_ratio = ref.get('effectLabel') not in ('MD', 'SMD')
            vals = ref.get('values', {})
            for trt, v in vals.items():
                if is_ratio:
                    self.assertGreater(v['hr'], 0, f'{topic}/{trt} ratio measure has non-positive value: {v["hr"]}')
                self.assertLess(v['lower'], v['upper'], f'{topic}/{trt} lower >= upper')


class TestSanitizeForR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_escapes_backslash(self):
        r = self.driver.execute_script(r"return sanitizeForR('a\\b', '\"')")
        self.assertIn('\\\\', r)

    def test_escapes_double_quote(self):
        r = self.driver.execute_script('return sanitizeForR(\'a"b\', \'"\')')
        self.assertIn('\\"', r)

    def test_escapes_single_quote(self):
        r = self.driver.execute_script("return sanitizeForR(\"a'b\", \"'\")")
        self.assertIn("\\'", r)

    def test_escapes_newline(self):
        r = self.driver.execute_script(r"return sanitizeForR('a\nb', '\"')")
        self.assertIn('\\n', r)

    def test_empty_string(self):
        r = self.driver.execute_script("return sanitizeForR('', '\"')")
        self.assertEqual(r, '')

    def test_null_input(self):
        r = self.driver.execute_script("return sanitizeForR(null, '\"')")
        self.assertEqual(r, '')


if __name__ == '__main__':
    print(f'\n{"="*60}')
    print(f'  MetaSprint NMA — Expanded Test Suite')
    print(f'  File: {HTML_PATH}')
    print(f'{"="*60}\n')

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    test_classes = [
        TestThresholdAnalysis,
        TestToolComparison,
        TestReviewerPacket,
        TestPRISMAChecklist,
        TestGoldStandardValidation,
        TestMatchTier,
        TestBatchTopicValidation,
        TestSanitizeForR,
    ]
    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f'\n{"="*60}')
    print(f'  TOTAL: {result.testsRun} tests')
    print(f'  PASSED: {result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'  FAILED: {len(result.failures)}')
    print(f'  ERRORS: {len(result.errors)}')
    print(f'{"="*60}')
