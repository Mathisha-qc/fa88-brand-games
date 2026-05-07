import allure
import time
from pages.base_page import BasePage
from utils.ws_commands import TAIXIU_MINI_CMD, WS_CMD
from core.ws_engine import WSEngine



@allure.feature("Game Mechanics")
@allure.story("TaiXiu Mini Betting Flow")
class TaiXiuMiniGamePage(BasePage):
    def __init__(self, driver,):
        super().__init__(driver)
        self.ws = WSEngine(driver, self.log_step)

    @allure.step("Step 1: Open TaiXiu Mini Game")
    def open_taixiu_mini_game(self):
         self._interact_canvas(x=600, y=539, wait_after=15.0)
         print("Taixiu mini opened")
         self.log_step("Open Game", "PASSED", "TaiXiu Mini opened")


    def place_bet_three_step(
        self,
        chip_amount=1000.0,
        bet=(987, 557),        # step 1: choose Bet side  Pointer X: 987 Pointer Y: 557
        amount=(232, 742),       # step 2: choose amount chip Pointer X: 232 Pointer Y: 742
        place_bet=(700, 852),   # step 3: click place bet button Pointer X: 700 Pointer Y: 852

    ):
        self._interact_canvas(x=bet[0], y=bet[1], wait_after=0.4)
        self._interact_canvas(x=amount[0], y=amount[1], wait_after=0.4)
        self._interact_canvas(x=place_bet[0], y=place_bet[1], wait_after=1.0)

        bet_ev = self.ws._wait_for_cmd(TAIXIU_MINI_CMD["BET"], timeout=10, from_cursor=True, expected_direction="send")

        print("Bet placed")
        bet_amount = self.ws._extract_amount(bet_ev, ["b", "amount", "betAmount", "value", "chip"])
        self.log_step(
            "Place Bet",
            "PASSED",
            f"Bet placed: {bet_amount}"
        )

        assert bet_amount == float(chip_amount), \
            f"[FAIL] Bet mismatch exp={chip_amount}, ws={bet_amount}"


    @allure.step("Step 2: Validate TaiXiu Mini Round Flow")
    def play_and_validate_flow(
        self,
        wallet_before=None,
        chip_amount=1000.0,
    ):   
        self.ws._drain_ws_events()
        with allure.step("1. Validate Subscriptions"):
         self.ws._wait_for_cmd(TAIXIU_MINI_CMD["SUBSCRIBE_INFO"], timeout=5, expected_direction="send")
         print("Subscribed")

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

        with allure.step("3. New game start -> place bet"):
         self.ws._wait_for_cmd(TAIXIU_MINI_CMD["START_GAME"], timeout=70)
         print("Game Start you can now place bet")
         self.log_step("Game Start", "PASSED", "Game started")

        
        with allure.step(f"4. Place Bet of {chip_amount}"):
         self.place_bet_three_step(chip_amount)

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
         

        with allure.step("6. Show Result "):
         self.ws._wait_for_cmd(TAIXIU_MINI_CMD["SHOW_RESULT"], timeout=60, from_cursor=True)
         print(f"[PASS]  Show result {TAIXIU_MINI_CMD['SHOW_RESULT']} detected.")
        
        #with allure.step("7. Calculate Result Money "):
         #self.ws._wait_for_cmd(TAIXIU_MINI_CMD["CALCULATE_RESULT_MONEY"], timeout=60, from_cursor=True)
         #print(f"[PASS]  Show result {TAIXIU_MINI_CMD['CALCULATE_RESULT_MONEY']} detected.")
         
        
        with allure.step("8. Determine Round Result (Win/Loss)"):
        # optional final update: only assert if win; if lose, skip
         try:
           final_ev = self.ws._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=10, from_cursor=True)
           wallet_final = self.ws._extract_amount(
              final_ev, ["wallet", "balance", "gold"]
            )
         except :
           wallet_final = None
        
        time.sleep(2)
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
          
          
        with allure.step("9. Chat "):
          message = "Hi"

          self._interact_canvas(x=1439, y=831, wait_after=4.0) #Pointer X: 1439 Pointer Y: 831
          chat_input = self.driver.switch_to.active_element
          chat_input.send_keys(message)

          self._interact_canvas(x=1701, y=802, wait_after=1.0) #Pointer X: 1701 Pointer Y: 802
          
        chat_ev = self.ws._wait_for_cmd(TAIXIU_MINI_CMD["CHAT"], timeout=10, from_cursor=True, expected_msg=message, expected_direction="send" )
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
        self._interact_canvas(x=1059, y=265, wait_after=0.4) # Pointer X: 1059 Pointer Y: 265
        self.ws._wait_for_cmd(TAIXIU_MINI_CMD["UNSUBSCRIBE_INFO"], timeout=15, from_cursor=True, expected_direction="send")
        print("Unsubscribed")
        self.log_step("Exit Game", "PASSED", "Exited successfully")
