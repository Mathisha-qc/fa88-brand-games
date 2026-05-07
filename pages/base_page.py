import time
from pathlib import Path
import allure

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from reports.custom_report import report , ReportStep


class BasePage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)
        self.CANVAS = (By.TAG_NAME, "canvas")

    # AUTO STEP + SCREENSHOT SYSTEM (CORE FEATURE)
    def step(self, name, status="PASSED", message="", extra=None, take_screenshot=True):

       try:
         path_str = None
         if take_screenshot:
             screenshot_dir  = Path("reports") / "screenshots" 
             screenshot_dir.mkdir(parents=True, exist_ok=True)

             # Screenshot name = GAME + STEP + TIMESTAMP
             file_name = f"{name}_{int(time.time())}.png"
             path = screenshot_dir  / file_name

             self.driver.save_screenshot(str(path))
             path_str = str(path)

         report.steps.append(
              ReportStep(
                name=name,
                status=status,
                message=message,
                screenshot=path_str,
                extra=extra
               )
            )

         return path_str

       except Exception as e:
        print(f"[STEP ERROR] {e}")

        report.steps.append(
            ReportStep(
                name=name,
                status="FAILED",
                message=str(e),
                extra=extra
            )
        )
        return None

    def log_step(self, name, status, message, extra=None, take_screenshot=True):
        """
        Use this everywhere instead of step()
        Adds:
        - Allure screenshot
        - Custom report logging
        """
        if take_screenshot:
          try:
             screenshot = self.driver.get_screenshot_as_png()
             allure.attach(
                screenshot,
                name=name,
                attachment_type=allure.attachment_type.PNG
             )
          except Exception:
             pass

        self.step(
            name=name,
            status=status,
            message=message,
            extra=extra,  # ✅ IMPORTANT for WS table
            take_screenshot=take_screenshot
        )
        
    
    # CANVAS INTERACTION 
    def _interact_canvas(self, x, y, text=None, wait_after=1.0):

        canvas = self.wait.until(
            EC.presence_of_element_located(self.CANVAS)
        )

        self.driver.execute_script(
            """
            const canvas = arguments[0];
            const x = arguments[1];
            const y = arguments[2];

            function fire(type) {
              const evt = new MouseEvent(type, {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: canvas.getBoundingClientRect().left + x,
                clientY: canvas.getBoundingClientRect().top + y
              });
              canvas.dispatchEvent(evt);
            }

            fire('mousemove');
            fire('mousedown');
            fire('mouseup');
            fire('click');
            """,
            canvas, x, y
        )

        if text:
            self.driver.execute_script(
                "document.activeElement && document.activeElement.focus();"
            )
            self.driver.switch_to.active_element.send_keys(text)

        time.sleep(wait_after)

    