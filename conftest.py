import pytest
import time
import os
import tempfile
import allure
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def pytest_configure(config):
    # This adds a custom 'Environment' section to your Allure Dashboard
    allure.dynamic.parameter("Browser", "Chrome")
    allure.dynamic.parameter("Environment", "Production")
    allure.dynamic.parameter("Game", "HitClub Xoc Dia")

@pytest.fixture(scope="session")
def driver():
    # 1. Setup Chrome Options
    chrome_options = Options()
    
    # This is the "Magic" flag that keeps the browser open after the script ends
    chrome_options.add_experimental_option("detach", True)

    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    chrome_options.add_experimental_option('perfLoggingPrefs', {'enableNetwork': True})
    
    # Create a unique profile directory for a fresh session every time
    unique_id = int(time.time())
    temp_profile = os.path.join(tempfile.gettempdir(), f"selenium_profile_{unique_id}")
    
    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-first-run")
    
    # 2. Initialize Driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 3. Explicitly enable Network domain for CDP events
    driver.execute_cdp_cmd("Network.enable", {})
    
    # 4. Provide the driver to the test
    yield driver
    
    # 5. Teardown
    # We print the info but DO NOT call driver.quit() or driver.close()
    print(f"\n[INFO] Test finished. Browser remains open.")
    print(f"[INFO] Profile Path: {temp_profile}")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Captures a screenshot for EVERY test result (Pass or Fail)
    and attaches it to the Allure report.
    """
    outcome = yield
    report = outcome.get_result()

    # We only take the screenshot at the very end of the test ('call' phase)
    if report.when == 'call':
        driver = item.funcargs.get('driver')
        if driver:
            try:
                # Determine the status for the label
                status_label = "PASS" if report.passed else "FAIL"
                
                # Attach the screenshot to the Allure report
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name=f"Final_Game_State_{status_label}",
                    attachment_type=allure.attachment_type.PNG
                )
                print(f"\nScreenshot captured for {status_label} result.")
            except Exception as e:
                print(f"Could not capture screenshot: {e}")