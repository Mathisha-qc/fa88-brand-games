import time
from pages.base_page import BasePage


class PopupHandler(BasePage):
    def clear_all_whenever(self, timeout=30):
        print("[INFO] Starting smart cleanup...")

        # Phase 1: one-time static popup clear
        print("[INFO] Clearing initial static popups (one-time)...")
        self._interact_canvas(x=1652, y=177, wait_after=1.5)  # Popup 1
        self._interact_canvas(x=1246, y=308, wait_after=1.5)  # Popup 3

        # Phase 2: monitor WS cmd=305 and clear invitation only when seen
        start_time = time.time()
        invitation_count = 0
        last_305_time = None

        while time.time() - start_time < timeout:
            if self.validate_ws_cmd("305"):
                print(f"[ALERT] CMD 305 detected. Clearing invitation {invitation_count + 1}...")
                self._interact_canvas(x=810, y=676, wait_after=2.0)
                invitation_count += 1
                last_305_time = time.time()

            # stop if no new 305 for 10s after first detection
            if last_305_time and (time.time() - last_305_time > 10):
                break

            time.sleep(0.5)

        print(f"[INFO] Cleanup finished. Invitations handled: {invitation_count}")
