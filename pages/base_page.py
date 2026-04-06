# pages/base_page.py
import json
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)
        self.CANVAS = (By.TAG_NAME, "canvas")

    def _interact_canvas(self, x, y, text=None, wait_after=1.0):
        """
        JS-based canvas click at absolute pixel coordinates inside canvas.
        x, y are canvas-local coordinates (top-left origin).
        """
        canvas = self.wait.until(EC.presence_of_element_located(self.CANVAS))

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
            self.driver.execute_script("document.activeElement && document.activeElement.focus();")
            self.driver.switch_to.active_element.send_keys(text)

        time.sleep(wait_after)

    def validate_ws_cmd(self, target_cmd):
        target_cmd = str(target_cmd)
        try:
            logs = self.driver.get_log("performance")
            for entry in logs:
                msg = json.loads(entry["message"]).get("message", {})
                method = msg.get("method")
                if method not in ("Network.webSocketFrameReceived", "Network.webSocketFrameSent"):
                    continue

                payload = msg.get("params", {}).get("response", {}).get("payloadData", "")
                if not payload:
                    continue

                try:
                    data = json.loads(payload)
                    if str(data.get("cmd", "")) == target_cmd:
                        return True
                except Exception:
                    if f'"cmd":{target_cmd}' in payload or f'"cmd":"{target_cmd}"' in payload:
                        return True
        except Exception:
            pass
        return False
