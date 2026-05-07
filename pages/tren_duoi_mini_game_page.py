import allure
import time
import cv2
import numpy as np
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\mathi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


from pages.base_page import BasePage
from utils.ws_commands import TREN_DUOI_CMD, WS_CMD
from core.ws_engine import WSEngine


@allure.feature("Game Mechanics")
@allure.story("Tren-Duoi Mini Betting Flow")
class TrenDuoiMiniGamePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.ws = WSEngine(driver, self.log_step)

    @allure.step("Step 1: Open Tren-Duoi Mini Game")
    def open_trenduoi_mini_game(self):
        self._interact_canvas(x=1680, y=986, wait_after=5.0)
        self._interact_canvas(x=1506, y=796, wait_after=15.0)
        print("Tren-Duoi mini opened")

    START_BTN_REGION = (834, 510, 260, 90)

    def _grab_screen_np(self):
        png = self.driver.get_screenshot_as_png()
        arr = np.frombuffer(png, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)

    def _is_start_enabled_by_ocr(self):
        x, y, w, h = self.START_BTN_REGION
        img = self._grab_screen_np()
        crop = img[y:y + h, x:x + w]

        cv2.imwrite(f"debug_crop_{np.random.randint(1000)}.png", crop)

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        gold_mask = cv2.inRange(hsv, (15, 70, 120), (40, 255, 255))
        gold_ratio = float(np.count_nonzero(gold_mask)) / float(gold_mask.size)
        v_mean = float(np.mean(hsv[:, :, 2]))  # brightness
       
       # ---------- text signal ----------
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        text_raw = pytesseract.image_to_string(th, config="--oem 3 --psm 7").upper()
        text = "".join(ch for ch in text_raw if ch.isalnum())  # normalize OCR noise

        has_start_text = (
          "BATDAU" in text
          or ("BAT" in text and "DAU" in text)
          or ("B" in text and "T" in text and "U" in text)
        )
    
        enabled = (gold_ratio > 0.40 and v_mean > 120) or (gold_ratio > 0.20 and has_start_text)


        self.log_step("OCR Start Button", "INFO", f"text='{text}', has_text={has_start_text}, gold_ratio={gold_ratio:.3f}, v_mean={v_mean:.1f}, enabled={enabled}")
        return enabled
        
    CARD_REGION = (900, 450, 80, 80) # (x, y, width, height) - Placeholder values!

    def _get_current_card_by_ocr(self):
        x, y, w, h = self.CARD_REGION
        img = self._grab_screen_np()
        crop = img[y:y + h, x:x + w]

        # CRITICAL DEBUGGING STEP: 
        # Check this image in your folder to make sure it ONLY shows the card letter/number!
        cv2.imwrite("debug_card_crop.png", crop)

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # Scale up heavily since card text might be small
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        
        # Thresholding (Depending on if the card is dark text on white, or white text on dark, 
        # you may need to add or remove cv2.bitwise_not(th) here)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Config: psm 8 = treat as a single word. Whitelist = only allow valid card characters.
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=2345678910JQKA'
        
        text_raw = pytesseract.image_to_string(th, config=custom_config).strip().upper()
        
        # Clean up the output to ensure we only get the alphanumeric part
        card_val = "".join(ch for ch in text_raw if ch.isalnum())

        self.log_step("OCR Card Reading", "INFO", f"Raw: '{text_raw}', Cleaned Card: '{card_val}'")
        return card_val
    
    def place_bet_step(
        self,
        chip_amount=1000.0,
        amount=(661, 455),          # step 1: choose chip (1k)
        place_bet=(964, 589),       # step 2: place bet
    ):
        self._interact_canvas(x=amount[0], y=amount[1], wait_after=0.4)
        self._interact_canvas(x=place_bet[0], y=place_bet[1], wait_after=1.0)

        bet_ev = self.ws._wait_for_cmd(TREN_DUOI_CMD["START_GAME"], timeout=10, from_cursor=True, expected_direction="send")
        print("Bet placed")
        bet_amount = self.ws._extract_amount(bet_ev, ["b", "amount", "betAmount", "value", "chip"])
        self.log_step("Place Bet", "PASSED", f"Bet placed: {bet_amount}")

        assert bet_amount == float(chip_amount), f"[FAIL] Bet mismatch exp={chip_amount}, ws={bet_amount}"

    @allure.step("Step 2: Repeat until WIN (STOP_GAME + 1503)")
    def play_until_win_1503(
        self,
        wallet_before=None,
        chip_amount=1000.0,
        max_attempts=20
    ):
        self.ws._drain_ws_events()

        with allure.step("1. Validate Subscriptions"):
           self.ws._wait_for_cmd(TREN_DUOI_CMD["INFO_GAME"], timeout=8, expected_direction="send")
           print("Subscribed")
           self.log_step("Open Game", "PASSED", "Tren-Duoi Mini opened")

        with allure.step("2. Wallet Balance Before Bet"):
         if wallet_before is None:
          before_ev = self.ws._wait_for_cmd(WS_CMD["USER_INFO"], timeout=10, from_cursor=False)
          wallet_before = self.ws._extract_amount(
             before_ev, ["wallet", "balance", "gold"]
          )

         assert wallet_before is not None, "[FAIL] Could not parse wallet_before."
         allure.attach(f"Wallet Before: {wallet_before}", name="Audit", attachment_type=allure.attachment_type.TEXT)
         print(f"[INFO] Wallet before bet: {wallet_before}")

         self.log_step("Wallet Before", "PASSED", str(wallet_before))

        for attempt in range(1, max_attempts + 1):
            with allure.step(f"Attempt {attempt} - Place Bet"):
                self.place_bet_step(chip_amount=chip_amount)

                after_bet_ev = self.ws._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=40, from_cursor=True)
                wallet_after_bet = self.ws._extract_amount(after_bet_ev, ["wallet", "balance", "gold"])
                assert wallet_after_bet is not None, "[FAIL] Could not parse wallet_after_bet"
                self.log_step(
                   "Wallet After Bet",
                   "PASSED",
                  f"{wallet_before} → {wallet_after_bet}"
                  )
                
            current_card = self._get_current_card_by_ocr()

            with allure.step(f"Attempt {attempt} - Press UP and check LOSS"):
                if current_card == "A":
                    self.log_step("Skip UP", "INFO", "Card is 'A', UP action skipped.")
                else:
                 self._interact_canvas(x=1241, y=535, wait_after=0.2)# Up
                 self.ws._wait_for_cmd(TREN_DUOI_CMD["START_ROUND"], timeout=10, from_cursor=True, expected_direction="send")
                 self.log_step(
                   "Press UP",
                   "PASSED",
                   "Up Button Pressed"
                   )
                
                time.sleep(3)

                # LOSS rule from you: if START enabled after UP => loss, re-bet
                if self._is_start_enabled_by_ocr():
                    self.log_step("Round Result", "INFO", f"LOSS after UP (attempt {attempt})")
                    continue

            with allure.step(f"Attempt {attempt} - Press DOWN and check LOSS"):
                if current_card == "2":
                    self.log_step("Skip DOWN", "INFO", "Card is '2', DOWN action skipped.")
                else:
                   self._interact_canvas(x=1235, y=675, wait_after=0.2) # DOWN
                   self.ws._wait_for_cmd(TREN_DUOI_CMD["START_ROUND"], timeout=10, from_cursor=True, expected_direction="send")
                   self.log_step(
                      "Press DOWN",
                      "PASSED",
                      "Down Button Pressed"
                    )
                time.sleep(3)

                # LOSS rule from you: if START enabled after DOWN => loss, re-bet
                if self._is_start_enabled_by_ocr():
                    self.log_step("Round Result", "INFO", f"LOSS after DOWN (attempt {attempt})")
                    continue

            time.sleep(5)
            with allure.step(f"Attempt {attempt} - Stop Game and validate WIN by 1503"):
                self._interact_canvas(x=1452, y=589, wait_after=5.0)  # STOP
                self.ws._wait_for_cmd(TREN_DUOI_CMD["STOP_GAME"], timeout=20, from_cursor=True, expected_direction="send")

                # WIN rule from you: STOP_GAME + 1503
                try:
                    final_ev = self.ws._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=5, from_cursor=True)
                    payout = self.ws._extract_amount(final_ev, ["amount", "gold", "value", "payout"])
                    self.log_step("Round Result", "PASSED", f"WIN attempt={attempt}, payout={payout}")
                    return
                except Exception:
                    self.log_step("Round Result", "INFO", f"After STOP_GAME (attempt {attempt}), retry")

        raise AssertionError(f"[FAIL] WIN condition not met within {max_attempts} attempts")

        

    @allure.step("Step 3: Exit Tren-Duoi Mini Game")
    def exit_game(self):
        self._interact_canvas(x=1394, y=455, wait_after=0.4)  # close
        print("Unsubscribed")
        self.log_step("Exit Game", "PASSED", "Exited successfully")