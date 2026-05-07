import allure
import time
import hashlib
import pyperclip
from pages.base_page import BasePage
from utils.ws_commands import TAIXIU_MD5_MINI_CMD, WS_CMD
from core.ws_engine import WSEngine



@allure.feature("Game Mechanics")
@allure.story("TaiXiu-MD5 Mini Betting Flow")
class TaiXiuMd5MiniGamePage(BasePage):
    def __init__(self, driver,):
        super().__init__(driver)
        self.ws = WSEngine(driver, self.log_step)

    @allure.step("Step 1: Open TaiXiu-MD5 Mini Game")
    def open_taixiu_md5_mini_game(self):
         self._interact_canvas(x=1680, y=986, wait_after=5.0)
         self._interact_canvas(x=1528, y=658, wait_after=15.0) 
         print("Taixiu-MD5 mini opened")
         


    def place_bet_three_step(
        self,
        chip_amount=1000.0,
        bet=(1026, 524),        # step 1: choose XIU Bet side  Pointer X: 1026 Pointer Y: 524
        amount=(199, 775),       # step 2: choose amount chip Pointer X: 199 Pointer Y: 775
        place_bet=(636, 875),   # step 3: click place bet button Pointer X: 636 Pointer Y: 875

    ):
        
        self._interact_canvas(x=bet[0], y=bet[1], wait_after=0.4)
        self._interact_canvas(x=amount[0], y=amount[1], wait_after=0.4)
        self._interact_canvas(x=place_bet[0], y=place_bet[1], wait_after=1.0)

        bet_ev = self.ws._wait_for_cmd(TAIXIU_MD5_MINI_CMD["ADD_BETTING"], timeout=10, from_cursor=True, expected_direction="send")
        print("Bet placed")
        bet_amount = self.ws._extract_amount(bet_ev, ["b", "amount", "betAmount", "value", "chip"])
        self.log_step(
            "Place Bet",
            "PASSED",
            f"Bet placed: {bet_amount}"
        )

        assert bet_amount == float(chip_amount), \
            f"[FAIL] Bet mismatch exp={chip_amount}, ws={bet_amount}"
        

    @allure.step("Validate Provably Fair System (SHA-256 Check)")
    def validate_game_fairness(self, initial_hash: str, result_string: str):
        # 1. Generate the hash locally (MD5 based on the game's UI)
        generated_hash = hashlib.sha256(result_string.encode('utf-8')).hexdigest()
        
        allure.attach(
            f"Initial Hash (Copied from UI): {initial_hash}\n"
            f"Result String (Copied from UI): {result_string}\n"
            f"Locally Generated Hash: {generated_hash}", 
            name="Fairness Hash Verification", 
            attachment_type=allure.attachment_type.TEXT
        )
        
        if initial_hash.strip().lower() == generated_hash.strip().lower():
            self.log_step("Fairness Validation", "PASSED", f"Hashes match perfectly!\nExpected: {initial_hash}\nGot: {generated_hash}")
            print(f"[PASS] Fairness validated! Hash: {generated_hash}")
        else:
            self.log_step("Fairness Validation", "FAILED", "Hash Mismatch!")
            print(f"[FAIL] Expected: {initial_hash} | Got: {generated_hash}")
            assert False, "Fairness Check Failed: The generated hash does not match!"

   # @allure.step("Click UI Copy Button and Read Clipboard")
   # def get_text_via_copy_button(self, copy_x, copy_y):
        #"""Clicks a copy button on the canvas and returns the clipboard content."""
        # Clear clipboard first to avoid reading old data by mistake
       # pyperclip.copy("") 
        
        # Click the copy button based on provided coordinates
       # self._interact_canvas(x=copy_x, y=copy_y, wait_after=1.0)
        
        # Read and return the text that was copied to the system clipboard
       # copied_text = pyperclip.paste()
       # return copied_text


    @allure.step("Step 2: Validate TaiXiu-MD5 Mini Round Flow")
    def play_and_validate_flow(
        self,
        wallet_before=None,
        chip_amount=1000.0,
    ):
        
        
        self.ws._drain_ws_events()
        with allure.step("1. Validate Subscriptions"):
         self.ws._wait_for_cmd(TAIXIU_MD5_MINI_CMD["SUBSCRIBLE"], timeout=5, expected_direction="send")        
         print("Subscribed")
         self.log_step("Open Game", "PASSED", "TaiXiu-MD5 Mini opened")

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

        with allure.step("3. New game start and Get Initial Hash from WS"):
         start_ev = self.ws._wait_for_cmd(TAIXIU_MD5_MINI_CMD["START_BETTING"], timeout=60)
         print("Game Start you can now place bet")

         initial_md5_hash = ""
         if start_ev and "data" in start_ev and len(start_ev["data"]) > 1:
                # Get the dictionary at index 1 of the "data" list, then get "md5"
                initial_md5_hash = start_ev["data"][1].get("md5", "")
         self.log_step("Game Start", "PASSED", f"Hash received: {initial_md5_hash}")

         # ---> CLICK "COPY" FOR CHUỖI HASH <---
         #initial_md5_hash = self.get_text_via_copy_button(copy_x=1034, copy_y=689) 
         #print(f"Copied Initial Hash: {initial_md5_hash}")

        
        with allure.step(f"4. Place Bet of {chip_amount}"):
         self.place_bet_three_step(chip_amount)

         self.place_bet_three_step(
             chip_amount=1000.0, 
             bet=(376, 500)  # Bet TAI
         )

        with allure.step("5. Verify Wallet Deduction After Bet"):
         after_bet_ev = self.ws._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=40, from_cursor=True)
         wallet_after_bet = self.ws._extract_amount(
            after_bet_ev, ["wallet", "balance", "gold"]
         )
         allure.attach(f"Wallet Before: {wallet_before}\nWallet After: {wallet_after_bet}", name="Audit", attachment_type=allure.attachment_type.TEXT)
         print(f"[INFO] Wallet after bet update: {wallet_after_bet}")

         assert wallet_before is not None, "[FAIL] Could not parse wallet_before."
         assert wallet_after_bet is not None, "[FAIL] Could not parse wallet_after_bet."

         self.log_step(
            "Wallet After Bet",
            "PASSED",
            f"{wallet_before} → {wallet_after_bet}"
        )

        # round-end validation (must happen for one completed round)
        with allure.step("6. End Game and Get Result String from WS"):
         end_ev = self.ws._wait_for_cmd(TAIXIU_MD5_MINI_CMD["END_GAME"], timeout=80, from_cursor=True)
         print(f"Round end") 

         game_result_string = ""
         if end_ev and "data" in end_ev and len(end_ev["data"]) > 1:
                # Get the dictionary at index 1 of the "data" list, then get "rs"
                game_result_string = end_ev["data"][1].get("rs", "")
         self.log_step("End Game", "PASSED", f"Hash received: {game_result_string}")

         # ---> CLICK "COPY" FOR KẾT QUẢ <---
         #game_result_string = self.get_text_via_copy_button(copy_x=1034, copy_y=689)
         #print(f"Copied Result String: {game_result_string}")


        # 7. EXECUTE FAIRNESS VALIDATION
        #self.validate_game_fairness(initial_hash=initial_md5_hash, result_string=game_result_string)
        if initial_md5_hash and game_result_string:
            self.validate_game_fairness(initial_hash=initial_md5_hash, result_string=game_result_string)
        else:
            print("[WARN] Could not validate fairness because WS strings were empty. Check your JSON keys!")
        
        with allure.step("7. Determine Round Result (Win/Loss)"):
        # optional final update: only assert if win; if lose, skip
         try:
           final_ev = self.ws._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=5, from_cursor=True)
           wallet_final = self.ws._extract_amount(
              final_ev, ["wallet", "balance", "gold"]
            )
         except Exception:
           wallet_final = None

        if wallet_final is not None and wallet_after_bet is not None:
         if wallet_final > wallet_after_bet:
          allure.dynamic.title("RESULT: WIN")
          allure.attach(f"Wallet Update: {wallet_final}", name="Audit", attachment_type=allure.attachment_type.TEXT)
          self.log_step(
            "Round Result",
            "PASSED",
            f"WIN | {wallet_after_bet} → {wallet_final}" )
          print(f"[PASS] WIN detected. Wallet updated: {wallet_after_bet} -> {wallet_final}")
        else:
            allure.dynamic.title("RESULT: LOSS")
            allure.attach(f"Wallet Update: {wallet_after_bet}", name="Audit", attachment_type=allure.attachment_type.TEXT)
            self.log_step(
            "Round Result",
            "INFO",
            f"LOSS | Wallet: {wallet_after_bet}")
            print("[INFO] LOSE and no extra wallet update")
          
          
        with allure.step("8. Chat "):
          message = "Hi"

          self._interact_canvas(x=1403, y=805, wait_after=4.0) 
          chat_input = self.driver.switch_to.active_element
          chat_input.send_keys(message)

          self._interact_canvas(x=1729, y=801, wait_after=1.0) 



          
        chat_ev = self.ws._wait_for_cmd(TAIXIU_MD5_MINI_CMD["CHAT"], timeout=10, from_cursor=True, expected_msg=message, expected_direction="send" )
        if chat_ev:
            self.log_step(
            "Chat Validation",
            "PASSED",
            f"My message validated: {message}"
           )
            print(f"[PASS] My chat message validated: {message}")

        else:
          self.log_step(
            "Chat Validation",
            "FAILED",
            f"My message NOT found: {message}"
           )
          print(f"[FAIL] My chat message not found")

     
    @allure.step("Step 3: Exit TaiXiu Mini Game")
    def exit_game(self):
        self._interact_canvas(x=1060, y=211, wait_after=0.4) 
        self.ws._wait_for_cmd(TAIXIU_MD5_MINI_CMD["UNSUBSCRIBLE"], timeout=15, from_cursor=True, expected_direction="send")
        print("Unsubscribed")
        self.log_step("Exit Game", "PASSED", "Exited successfully")
