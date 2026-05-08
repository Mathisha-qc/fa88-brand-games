import pytest
import time
import os
import tempfile
import shutil
import zipfile
import allure
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.screen_recorder import ScreenRecorder
from reports.custom_report import report, write_html_report



def pytest_configure(config):
    # This adds a custom 'Environment' section to your Allure Dashboard
    report.title = "HitClub Automation Report"
    report.base_url = "https://v.hitclub.sc/"
    report.username = "Mathisha1"
    report.browser_name = "Chrome"
    report.captcha_mode = "Manual"
    report.game_name = "Lobby"   # default (will override per game)

    # ✅ ALLURE ENV
    allure.dynamic.parameter("Browser", report.browser_name)
    allure.dynamic.parameter("Environment", "Production")

@pytest.fixture(scope="session")
def driver():
    # 1. Setup Chrome Options
    chrome_options = Options()
    
    # This is the "Magic" flag that keeps the browser open after the script ends
    chrome_options.add_experimental_option("detach", True)

    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'INFO'})
    chrome_options.add_experimental_option('perfLoggingPrefs', {'enableNetwork': True})

    #ALLOW CLIPBOARD ACCESS
    prefs = {
        "profile.default_content_setting_values.clipboard": 1  # 1 = ALLOW, 2 = BLOCK
    }
    # Note: If you already have other preferences, add them to this dictionary
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Create a unique profile directory for a fresh session every time
    unique_id = int(time.time())
    temp_profile = os.path.join(tempfile.gettempdir(), f"selenium_profile_{unique_id}")
    
    chrome_options.add_argument(f"--user-data-dir={temp_profile}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    
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



# FINAL TEST RESULT + ALLURE

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield
    result = outcome.get_result()

    if result.when != "call":
        return

    driver = item.funcargs.get("driver")
    

    if not driver:
        return

    status = "PASSED" if result.passed else "FAILED"

    try:
        # ✅ Save final screenshot directly to the dynamic run directory
        screenshot_dir = report.run_dir / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = screenshot_dir / f"FINAL_{item.name}.png"
        driver.save_screenshot(str(screenshot_path))

        allure.attach(
            screenshot_path.read_bytes(),
            name=f"Final_{status}",
            attachment_type=allure.attachment_type.PNG
        )

        # ✅ Ensure the final screenshot is tracked by custom_report
        report.add_step(
            name="Final Test Execution Screenshot",
            status=status,
            message=f"Test finished with status: {status}",
            screenshot=str(screenshot_path)
        )

    except Exception as e:
        print(f"[ERROR] Screenshot failed: {e}")
   


# TEST START/END TRACKING
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):

   # 1. Get the driver from the current test
    driver = item.funcargs.get("driver")
    recorder = None
    video_path = None

    if driver:
        # 2. SETUP VIDEO PATH & START RECORDING
        video_path = report.run_dir / f"{item.name}.webm"
        
        # ✅ FIX: Pass BOTH the driver and the path
        recorder = ScreenRecorder(driver, str(video_path))
        recorder.start()

    report.add_step(
        name=item.name,
        status="INFO",
        message="Test started"
    )

    yield

    # 3. STOP RECORDING & SAVE TO REPORT
    if recorder:
        recorder.stop()
        report.video_path = str(video_path)

    report.add_step(
        name=item.name,
        status="INFO",
        message="Test finished"
    )
   

# GENERATE HTML REPORT, ZIP & CLEANUP
def pytest_sessionfinish(session, exitstatus):

    final_status = "PASSED" if exitstatus == 0 else "FAILED"
    report.finish(final_status)

    output_dir = report.run_dir
    path = write_html_report(report, output_dir)

    try:
        # 1. CREATE THE PERFECT ZIP FILE FOR SHARING
        safe_game_name = report.game_name.replace(" ", "_") if report.game_name else "Game"
        zip_name = f"reports/{safe_game_name}_Report_{int(time.time())}.zip"
        zip_path = Path(zip_name).resolve()
        
        import zipfile
        import os
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
                    
        print(f"\n PERFECT ZIP CREATED: {zip_path}")

        # 2. RENAME TEMP FOLDER TO 'latest_run' INSTEAD OF DELETING IT
        import shutil
        latest_dir = Path("reports/latest_run")
        
        # Delete the previous run's viewable folder if it exists
        if latest_dir.exists():
            shutil.rmtree(latest_dir)
            
        # Move our new temp folder to become the latest run
        if "temp_run" in str(output_dir.name):
            output_dir.rename(latest_dir)
            print(" Temporary directory moved to 'latest_run' for viewing.")
        
        # 3. OPEN THE LOCAL HTML FILE IN CHROME
        import webbrowser
        final_html_path = latest_dir / "custom_report.html"
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
        webbrowser.get(chrome_path).open(final_html_path.resolve().as_uri())

    except Exception as e:
        print(f"[ERROR] Session finish failed: {e}")

    