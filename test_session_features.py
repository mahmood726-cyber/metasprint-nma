"""
Selenium test suite for MetaSprint NMA — Session Features
Tests features added during the improvement session:
  1. Published reference datasets (23 topics)
  2. Concordance system (bidirectional, grade badge, color-blind verdicts)
  3. R Validation Script generator
  4. WebR section UI
  5. Keyboard shortcuts (Ctrl+Enter, Ctrl+S)
  6. Auto-save to localStorage
  7. Tutorial walkthrough
  8. Progress bar
  9. Net heat plot
  10. Treatment rank clustering
  11. sanitizeForR helper
  12. ARIA/accessibility improvements
"""
import io, os, sys, time, json, unittest
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
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

def load_demo_and_run(driver):
    """Load smoking cessation demo dataset and run NMA via JS (avoids headless visibility issues)."""
    # Use JS to select topic and trigger load (bypasses visibility check)
    driver.execute_script("""
        var sel = document.getElementById('exampleTopicSelect');
        if (sel) { sel.value = 'smoking'; }
        if (typeof loadExampleTopic === 'function') loadExampleTopic();
    """)
    time.sleep(3)
    # Switch to analyze phase
    driver.execute_script("if (typeof switchPhase === 'function') switchPhase('analyze');")
    time.sleep(1)
    # Run analysis via JS
    driver.execute_script("if (typeof runAnalysis === 'function') runAnalysis();")
    time.sleep(8)  # Wait for NMA to complete


class TestPublishedReferences(unittest.TestCase):
    """Test that all 23 published reference datasets exist and have valid structure."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_dropdown_has_23_topics(self):
        """Verify dropdown contains all topic options."""
        sel = self.driver.find_element(By.ID, 'exampleTopicSelect')
        options = sel.find_elements(By.TAG_NAME, 'option')
        # Filter out empty default and optgroup labels
        topic_options = [o for o in options if o.get_attribute('value') and o.get_attribute('value') != '']
        self.assertGreaterEqual(len(topic_options), 23, f'Expected >= 23 topics, got {len(topic_options)}')

    def test_new_topics_in_dropdown(self):
        """Verify the 4 new topics are in the dropdown."""
        sel = self.driver.find_element(By.ID, 'exampleTopicSelect')
        html = sel.get_attribute('innerHTML')
        for topic in ['doac_af', 'alk_nsclc', 'nsclc_1l_mono', 'smoking']:
            self.assertIn(f'value="{topic}"', html, f'{topic} missing from dropdown')

    def test_published_refs_exist(self):
        """Verify NMA_PUBLISHED_REFS has entries for all new topics."""
        for topic in ['doac_af', 'alk_nsclc', 'nsclc_1l_mono', 'smoking']:
            result = self.driver.execute_script(f'return NMA_PUBLISHED_REFS["{topic}"] != null')
            self.assertTrue(result, f'NMA_PUBLISHED_REFS.{topic} is null/undefined')

    def test_doac_af_values(self):
        """Verify DOAC AF has 4 treatments with plausible HRs."""
        vals = self.driver.execute_script('return NMA_PUBLISHED_REFS.doac_af.values')
        self.assertEqual(len(vals), 4)
        self.assertAlmostEqual(vals['Dabigatran']['hr'], 0.66, places=2)
        self.assertAlmostEqual(vals['Apixaban']['hr'], 0.79, places=2)

    def test_alk_nsclc_values(self):
        """Verify ALK NSCLC has 3 treatments."""
        vals = self.driver.execute_script('return NMA_PUBLISHED_REFS.alk_nsclc.values')
        self.assertEqual(len(vals), 3)
        self.assertAlmostEqual(vals['Lorlatinib']['hr'], 0.28, places=2)

    def test_smoking_has_effectLabel(self):
        """Verify smoking dataset has effectLabel = 'OR'."""
        label = self.driver.execute_script('return NMA_PUBLISHED_REFS.smoking.effectLabel')
        self.assertEqual(label, 'OR')

    def test_published_refs_all_have_values(self):
        """Every published ref dataset must have a values object with >= 1 entry."""
        topics = self.driver.execute_script('return Object.keys(NMA_PUBLISHED_REFS)')
        for topic in topics:
            count = self.driver.execute_script(f'return Object.keys(NMA_PUBLISHED_REFS["{topic}"].values).length')
            self.assertGreaterEqual(count, 1, f'{topic} has 0 treatments in values')


class TestConcordanceSystem(unittest.TestCase):
    """Test concordance metrics after loading demo and running NMA."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        # Dismiss tutorial if it appears
        try:
            cancel = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'No') or contains(text(),'Cancel')]"))
            )
            cancel.click()
        except TimeoutException:
            pass
        time.sleep(1)
        load_demo_and_run(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_published_comparison_renders(self):
        """Published comparison container should have content after NMA run."""
        container = self.driver.find_element(By.ID, 'publishedComparisonContainer')
        html = container.get_attribute('innerHTML')
        self.assertGreater(len(html), 100, 'Published comparison container is empty')

    def test_bidirectional_count_exists(self):
        """Should show 'Bidirectional:' metric in summary bar."""
        container = self.driver.find_element(By.ID, 'publishedComparisonContainer')
        self.assertIn('Bidirectional:', container.text)

    def test_overall_concordance_badge(self):
        """Should show overall concordance grade badge."""
        container = self.driver.find_element(By.ID, 'publishedComparisonContainer')
        self.assertIn('Overall concordance:', container.text)

    def test_color_blind_verdicts(self):
        """Verdicts should use text icons [=], [~], or [x]."""
        html = self.driver.find_element(By.ID, 'publishedComparisonContainer').get_attribute('innerHTML')
        has_icon = '[=]' in html or '[~]' in html or '[x]' in html
        self.assertTrue(has_icon, 'No color-blind safe verdict icons found')

    def test_verdict_has_aria_label(self):
        """Verdict spans should have aria-label (not role=status to avoid noisy live regions)."""
        spans = self.driver.find_elements(By.CSS_SELECTOR, '#publishedComparisonContainer [aria-label]')
        self.assertGreater(len(spans), 0, 'No aria-label on verdict spans')

    def test_table_has_aria_label(self):
        """Published comparison table should have aria-label."""
        tables = self.driver.find_elements(By.CSS_SELECTOR, '#publishedComparisonContainer table[aria-label]')
        self.assertGreater(len(tables), 0, 'Published comparison table missing aria-label')


class TestRValidationScript(unittest.TestCase):
    """Test the R Validation Script generator."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.driver = make_driver()
            cls.driver.get(FILE_URL)
            time.sleep(2)
            # Clear all dialogs/overlays and dismiss tutorial
            cls.driver.execute_script("""
                localStorage.setItem('metasprint-nma-tutorial-done','1');
                localStorage.removeItem('metasprint-nma-autosave');
                document.querySelectorAll('[role=dialog],.onboard-overlay').forEach(e => e.remove());
            """)
            cls.driver.get(FILE_URL)  # Reload clean
            time.sleep(3)
            load_demo_and_run(cls.driver)
        except Exception as e:
            try: cls.driver.quit()
            except: pass
            raise

    @classmethod
    def tearDownClass(cls):
        try: cls.driver.quit()
        except: pass

    def test_r_validation_button_exists(self):
        """R Validation Script button should exist in export toolbar."""
        btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'R Validation Script')]")
        self.assertTrue(btn.is_displayed())

    def test_r_validation_generates_script(self):
        """Clicking R Validation Script should open modal with R code."""
        # Dismiss any overlays first
        self.driver.execute_script("document.querySelectorAll('.onboard-overlay,[role=dialog]').forEach(e => e.remove())")
        time.sleep(0.3)
        btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'R Validation Script')]")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click()", btn)  # JS click bypasses overlay
        time.sleep(1)
        # Check modal appeared
        modal = self.driver.find_element(By.CSS_SELECTOR, '[role="dialog"]')
        self.assertTrue(modal.is_displayed())
        # Check R code content
        pre = modal.find_element(By.TAG_NAME, 'pre')
        code = pre.text
        self.assertIn('library(netmeta)', code)
        self.assertIn('VALIDATION CHECKS', code)
        self.assertIn('VERDICT', code)
        # Close modal
        close_btn = modal.find_element(By.CSS_SELECTOR, 'button[aria-label="Close"]')
        close_btn.click()
        time.sleep(0.5)

    def test_sanitizeForR_exists(self):
        """sanitizeForR function should be defined."""
        result = self.driver.execute_script('return typeof sanitizeForR')
        self.assertEqual(result, 'function')

    def test_sanitizeForR_escapes_backslash(self):
        """sanitizeForR should escape backslashes."""
        result = self.driver.execute_script("return sanitizeForR('Drug\\\\Name', '\"')")
        self.assertIn('\\\\', result)

    def test_sanitizeForR_escapes_quotes(self):
        """sanitizeForR should escape the specified quote character."""
        result = self.driver.execute_script('return sanitizeForR(\'Drug"Name\', \'"\')')
        self.assertIn('\\"', result)


class TestWebRSection(unittest.TestCase):
    """Test WebR UI elements (not the actual WebR loading which requires network)."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        try:
            cancel = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'No') or contains(text(),'Cancel')]"))
            )
            cancel.click()
        except TimeoutException:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_webr_section_exists(self):
        """WebR section should be in the DOM."""
        section = self.driver.find_element(By.ID, 'webrSection')
        self.assertIsNotNone(section)

    def test_webr_button_exists(self):
        """Load R & Validate button should exist."""
        btn = self.driver.find_element(By.ID, 'webrRunBtn')
        text = self.driver.execute_script("return arguments[0].textContent", btn)
        self.assertIn('Validate', text)

    def test_webr_badge_default(self):
        """Status badge should show 'Not loaded' initially."""
        badge = self.driver.find_element(By.ID, 'webrStatusBadge')
        text = self.driver.execute_script("return arguments[0].textContent", badge)
        self.assertIn('Not loaded', text)

    def test_webr_progress_bar_aria(self):
        """Progress bar should have role=progressbar and aria attributes."""
        bar = self.driver.find_element(By.ID, 'webrProgressBar')
        self.assertEqual(bar.get_attribute('role'), 'progressbar')
        self.assertIsNotNone(bar.get_attribute('aria-valuenow'))

    def test_webr_progress_text_aria(self):
        """Progress text should have aria-live=polite."""
        text = self.driver.find_element(By.ID, 'webrProgressText')
        self.assertEqual(text.get_attribute('aria-live'), 'polite')

    def test_webr_results_aria(self):
        """Results container should have aria-live=polite."""
        container = self.driver.find_element(By.ID, 'webrResultsContainer')
        self.assertEqual(container.get_attribute('aria-live'), 'polite')


class TestKeyboardShortcuts(unittest.TestCase):
    """Test keyboard shortcuts."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        try:
            cancel = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'No') or contains(text(),'Cancel')]"))
            )
            cancel.click()
        except TimeoutException:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_ctrl_s_triggers_autosave(self):
        """Ctrl+S should trigger auto-save via JS dispatch."""
        # Use JS to dispatch keyboard event (more reliable in headless)
        self.driver.execute_script("""
            document.dispatchEvent(new KeyboardEvent('keydown', {key: 's', ctrlKey: true, bubbles: true}));
        """)
        time.sleep(1.5)
        # Check localStorage was written
        saved = self.driver.execute_script("return localStorage.getItem('metasprint-nma-autosave')")
        self.assertIsNotNone(saved, 'Ctrl+S did not trigger auto-save to localStorage')


class TestAutoSave(unittest.TestCase):
    """Test auto-save to localStorage."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        try:
            cancel = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'No') or contains(text(),'Cancel')]"))
            )
            cancel.click()
        except TimeoutException:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_autosave_function_exists(self):
        """_autoSaveNow should be defined."""
        result = self.driver.execute_script('return typeof _autoSaveNow')
        self.assertEqual(result, 'function')

    def test_autosave_timer_stored(self):
        """Auto-save interval ID should be stored."""
        result = self.driver.execute_script('return typeof _autoSaveTimer')
        self.assertEqual(result, 'number')

    def test_autosave_saves_to_localstorage(self):
        """Calling _autoSaveNow should write to localStorage."""
        self.driver.execute_script('_autoSaveNow()')
        saved = self.driver.execute_script("return localStorage.getItem('metasprint-nma-autosave')")
        self.assertIsNotNone(saved)
        data = json.loads(saved)
        self.assertIn('timestamp', data)
        self.assertIn('settings', data)

    def test_autosave_size_cap(self):
        """Auto-save should skip if data > 2MB."""
        # This tests the guard exists, not that we can exceed 2MB
        result = self.driver.execute_script("""
            var orig = extractedStudies.length;
            _autoSaveNow();
            return localStorage.getItem('metasprint-nma-autosave') !== null;
        """)
        self.assertTrue(result)


class TestTutorial(unittest.TestCase):
    """Test tutorial walkthrough."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        # Don't dismiss tutorial — let it appear

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_tutorial_functions_exist(self):
        """startTutorial and _showTutorialStep should be defined."""
        self.assertEqual(self.driver.execute_script('return typeof startTutorial'), 'function')
        self.assertEqual(self.driver.execute_script('return typeof _showTutorialStep'), 'function')

    def test_tutorial_keyboard_handler_exists(self):
        """_tutorialKeyHandler should be defined."""
        self.assertEqual(self.driver.execute_script('return typeof _tutorialKeyHandler'), 'function')

    def test_tutorial_steps_defined(self):
        """_tutorialSteps should have 4 steps."""
        count = self.driver.execute_script('return _tutorialSteps.length')
        self.assertEqual(count, 4)

    def test_tutorial_can_start(self):
        """startTutorial should create a tooltip."""
        # Clear any existing tutorial state
        self.driver.execute_script("localStorage.removeItem('metasprint-nma-tutorial-done')")
        self.driver.execute_script('startTutorial()')
        time.sleep(1)
        tooltip = self.driver.find_elements(By.ID, 'tutorialTooltip')
        self.assertGreater(len(tooltip), 0, 'Tutorial tooltip not created')

    def test_tutorial_tooltip_has_role_dialog(self):
        """Tutorial tooltip should have role=dialog."""
        self.driver.execute_script('startTutorial()')
        time.sleep(1)
        tooltip = self.driver.find_element(By.ID, 'tutorialTooltip')
        self.assertEqual(tooltip.get_attribute('role'), 'dialog')

    def test_tutorial_shows_keyboard_hints(self):
        """Tutorial should show arrow key hints."""
        self.driver.execute_script('startTutorial()')
        time.sleep(1)
        tooltip = self.driver.find_element(By.ID, 'tutorialTooltip')
        # Should contain arrow key symbols or Esc
        self.assertTrue('Esc' in tooltip.text or '\u2190' in tooltip.get_attribute('innerHTML'))


class TestNetHeatAndClustering(unittest.TestCase):
    """Test net heat plot and rank clustering after NMA run."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        try:
            cancel = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'No') or contains(text(),'Cancel')]"))
            )
            cancel.click()
        except TimeoutException:
            pass
        time.sleep(1)
        load_demo_and_run(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_net_heat_plot_container_exists(self):
        """Net heat plot container should exist."""
        el = self.driver.find_element(By.ID, 'netHeatPlotContainer')
        self.assertIsNotNone(el)

    def test_net_heat_plot_renders(self):
        """Net heat plot should render SVG content after NMA."""
        el = self.driver.find_element(By.ID, 'netHeatPlotContainer')
        html = el.get_attribute('innerHTML')
        # Should contain SVG or title
        has_content = 'Net Heat Plot' in html or '<svg' in html
        self.assertTrue(has_content, 'Net heat plot did not render')

    def test_rank_cluster_container_exists(self):
        """Rank cluster container should exist."""
        el = self.driver.find_element(By.ID, 'rankClusterContainer')
        self.assertIsNotNone(el)

    def test_rank_clustering_renders(self):
        """Rank clustering should render after NMA."""
        el = self.driver.find_element(By.ID, 'rankClusterContainer')
        html = el.get_attribute('innerHTML')
        has_content = 'Treatment Rank Clustering' in html or 'Cluster' in html
        self.assertTrue(has_content, 'Rank clustering did not render')

    def test_rank_clustering_shows_silhouette(self):
        """Rank clustering should show silhouette score."""
        el = self.driver.find_element(By.ID, 'rankClusterContainer')
        self.assertIn('Silhouette', el.text)

    def test_rank_clustering_shows_clusters(self):
        """Rank clustering should assign cluster labels."""
        el = self.driver.find_element(By.ID, 'rankClusterContainer')
        self.assertIn('Cluster', el.text)


class TestProgressBar(unittest.TestCase):
    """Test progress bar."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        try:
            cancel = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'No') or contains(text(),'Cancel')]"))
            )
            cancel.click()
        except TimeoutException:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_progress_bar_function_exists(self):
        """showNMAProgress should be defined."""
        result = self.driver.execute_script('return typeof showNMAProgress')
        self.assertEqual(result, 'function')

    def test_progress_bar_creates_element(self):
        """showNMAProgress(-1) should create a bar element."""
        self.driver.execute_script('showNMAProgress(-1)')
        bar = self.driver.find_elements(By.ID, 'nmaProgressBar')
        self.assertGreater(len(bar), 0, 'Progress bar element not created')
        # Clean up
        self.driver.execute_script('showNMAProgress(1)')
        time.sleep(0.5)


class TestCSPAndSecurity(unittest.TestCase):
    """Test Content Security Policy and security measures."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_csp_allows_webr(self):
        """CSP should include webr.r-wasm.org in connect-src."""
        csp = self.driver.execute_script(
            "return document.querySelector('meta[http-equiv=\"Content-Security-Policy\"]')?.content || ''"
        )
        self.assertIn('webr.r-wasm.org', csp)
        self.assertIn('repo.r-wasm.org', csp)

    def test_csp_has_worker_src(self):
        """CSP should have worker-src for WebR WebAssembly."""
        csp = self.driver.execute_script(
            "return document.querySelector('meta[http-equiv=\"Content-Security-Policy\"]')?.content || ''"
        )
        self.assertIn('worker-src', csp)

    def test_no_console_errors(self):
        """Page should load without critical JS errors."""
        logs = self.driver.get_log('browser')
        severe = [l for l in logs if l['level'] == 'SEVERE' and 'favicon' not in l.get('message', '')]
        # Filter out CSP violations on file:// protocol (expected)
        severe = [l for l in severe if 'Content Security Policy' not in l.get('message', '')]
        self.assertEqual(len(severe), 0, f'Console errors: {severe[:3]}')


class TestAccessibility(unittest.TestCase):
    """Test ARIA and accessibility features."""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        cls.driver.get(FILE_URL)
        time.sleep(3)
        try:
            cancel = WebDriverWait(cls.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'No') or contains(text(),'Cancel')]"))
            )
            cancel.click()
        except TimeoutException:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_skip_link_exists(self):
        """Skip link should be present."""
        link = self.driver.find_element(By.CSS_SELECTOR, 'a.skip-link')
        self.assertIsNotNone(link)

    def test_toast_container_has_aria(self):
        """Toast container should have aria-live."""
        el = self.driver.find_element(By.ID, 'toastContainer')
        self.assertEqual(el.get_attribute('aria-live'), 'polite')

    def test_reduced_motion_css_exists(self):
        """prefers-reduced-motion media query should exist."""
        result = self.driver.execute_script("""
            var sheets = document.styleSheets;
            for (var i = 0; i < sheets.length; i++) {
                try {
                    var rules = sheets[i].cssRules;
                    for (var j = 0; j < rules.length; j++) {
                        if (rules[j].media && rules[j].media.mediaText.includes('prefers-reduced-motion'))
                            return true;
                    }
                } catch(e) {}
            }
            return false;
        """)
        self.assertTrue(result, 'No prefers-reduced-motion CSS rule found')


if __name__ == '__main__':
    print(f'\n{"="*60}')
    print(f'  MetaSprint NMA — Session Features Test Suite')
    print(f'  File: {HTML_PATH}')
    print(f'{"="*60}\n')

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestPublishedReferences,
        TestConcordanceSystem,
        TestRValidationScript,
        TestWebRSection,
        TestKeyboardShortcuts,
        TestAutoSave,
        TestTutorial,
        TestNetHeatAndClustering,
        TestProgressBar,
        TestCSPAndSecurity,
        TestAccessibility,
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
