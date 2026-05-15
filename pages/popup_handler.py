import time
from pages.base_page import BasePage
from utils.ws_commands import WS_CMD
from core.ws_engine import WSEngine


class PopupHandler(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.ws = WSEngine(driver, self.log_step)


    def clear_all_whenever(self, timeout=30):
        print("[INFO] Starting smart cleanup...")

        handled_305 = False
        received_306 = False

        # static popup clear
        #self._interact_canvas(x=1652, y=177, wait_after=3)  # Popup 1
        #print("warning popup cleared")
        

        # FIRST chance to catch 305
        print("[INFO] Checking CMD 305 (before UI)...")

        try:
          ev_305 = self.ws._wait_for_cmd(
            WS_CMD["INVITATION"],
            timeout=3,
            from_cursor=True,
          )

          if ev_305:
              handled_305 = True
              print("[ALERT] CMD 305 detected → clicking")

              self._interact_canvas(x=812, y=671, wait_after=2)

              try:
                 ev_306 = self.ws._wait_for_cmd(
                    WS_CMD["INVITATION_CONFIRM"],
                    timeout=5,
                    from_cursor=True,
                    expected_direction="send"
                  )
                 if ev_306:
                    received_306 = True
                    print("[SUCCESS] CMD 306 received")
              except AssertionError:
                print("[WARN] 306 not received")

        except AssertionError:
          print("[INFO] No CMD 305 (before UI)")

        # UI popup (use OpenCV here ideally, but keeping your current logic)
        print("[INFO] Handling UI popup...")
        self._interact_canvas(x=1246, y=308, wait_after=10)

        # SECOND chance to catch 305 (ONLY if not already handled)
        if not handled_305 or not received_306:
          print("[INFO] Checking CMD 305 (after UI)...")

          try:
              ev_305 = self.ws._wait_for_cmd(
                WS_CMD["INVITATION"],
                timeout=3,
                from_cursor=True
               )

              if ev_305 :
            
                print("[ALERT] CMD 305 detected after UI → clicking")

                self._interact_canvas(x=812, y=671, wait_after=5)

                self.ws._wait_for_cmd(
                    WS_CMD["INVITATION_CONFIRM"],
                    timeout=5,
                    from_cursor=True,
                    expected_direction="send"
                )
                print("[SUCCESS] CMD 306 received")
                
          except AssertionError:
              print("[INFO] No CMD 305 (after UI)")

    print("[INFO] Cleanup finished.")