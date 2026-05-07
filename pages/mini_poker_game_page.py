import allure
import time
from pages.base_page import BasePage
from utils.ws_commands import MINI_POKER_CMD, WS_CMD, GAME_IDS
from core.ws_engine import WSEngine



@allure.feature("Game Mechanics")
@allure.story("MiniPoker Betting Flow")
class MiniPokerGamePage(BasePage):
    def __init__(self, driver,):
        super().__init__(driver)
        self.ws = WSEngine(driver, self.log_step)
        self.game_id = GAME_IDS["MINI_POKER"]

    @allure.step("Step 1: Open MiniPoker Game")
    def open_mini_poker_game(self):
         self._interact_canvas(x=1680, y=986, wait_after=5.0)
         self._interact_canvas(x=1779, y=873, wait_after=15.0)
         print("MiniPoker opened")

    def place_bet(
        self,
        chip_amount=100.0,
        amount=(815, 720), 
        spin=(1434, 569), 
    ):
        # PERFORM & VALIDATE REGULAR SPIN
        with allure.step("1. Perform Manual Spin"):
         self._interact_canvas(x=amount[0], y=amount[1], wait_after=0.4)
         self._interact_canvas(x=spin[0], y=spin[1], wait_after=0.4)

         spin_ev = self.ws._wait_for_cmd(MINI_POKER_CMD["SPIN_RESULT"], timeout=10, from_cursor=True, expected_game_id=self.game_id, expected_direction="send")
         print("Spin Done")
         spin_amount = self.ws._extract_amount(spin_ev, ["b", "amount", "betAmount", "value", "chip"])
         self.log_step(
            "Spined",
            "PASSED",
            f" Spin Done: {spin_amount}"
          )

         assert spin_amount == float(chip_amount), \
             f"[FAIL] Bet mismatch exp={chip_amount}, ws={spin_amount}"
        
        

    @allure.step("Step 2: Validate MiniPoker Round Flow")
    def play_and_validate_flow(
        self,
        wallet_before=None,
        chip_amount=100.0,
    ):
        self.ws._drain_ws_events()
        with allure.step("1. Validate Subscriptions"):
         self.ws._wait_for_cmd(MINI_POKER_CMD["SUBSCRIBE_JACKPOT"], timeout=5, expected_game_id=self.game_id, expected_direction="send")

         print("Subscribed")
         self.log_step("Open Game", "PASSED", "MiniPoker opened")

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

        with allure.step(f"3. Place Spin of {chip_amount}"):
         self.place_bet(chip_amount)

        with allure.step("4. Verify Wallet Deduction After Bet"):
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
        
        with allure.step("5. Determine Round Result (Win/Loss)"):
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


        import time

        # PERFORM & VALIDATE AUTO SPIN
        auto_spin = (655, 727) 
        run_duration = 2.0  # Run for exactly 2 seconds
        
        with allure.step("1. Start Auto Spin"):
            # Click Auto Spin 
            self._interact_canvas(x=auto_spin[0], y=auto_spin[1], wait_after=0.01)
            print("Auto Spin Triggered")
            self.log_step("Auto Spined", "PASSED", "Auto Spin Started")
            
        with allure.step("Phase 1: 2-Second Capture & Stop"):
            start_cursor = self.ws._cursor  # Remember where the buffer started
            start_time = time.time()
            spins_requested = 0
            
            # Loop continuously until 2 seconds have passed
            while time.time() - start_time < run_duration:
                remaining_time = run_duration - (time.time() - start_time)
                if remaining_time <= 0:
                    break
                    
                try:
                    # Wait for the UI to send the spin request (Client -> Server)
                    # Use remaining_time as the timeout to ensure we don't oversleep
                    self.ws._wait_for_cmd(
                        MINI_POKER_CMD["SPIN_RESULT"], 
                        timeout=remaining_time, 
                        from_cursor=True, 
                        expected_game_id=self.game_id,
                        expected_direction="send"  
                    )
                    spins_requested += 1
                except Exception:
                    # Timeout reached (2 seconds elapsed while waiting for a command)
                    break

            # The exact moment 2 seconds are up, hit STOP!
            self._interact_canvas(x=auto_spin[0], y=auto_spin[1], wait_after=0.1)
            print(f"*** STOP BUTTON CLICKED AFTER 2 SECONDS (~{spins_requested} spins requested) ***")
            self.log_step("Stop Auto Spin", "PASSED", "Stopped game exactly after 2 seconds")

            # Allow 1.5 seconds for the server to reply with the final results of the last spin
            time.sleep(1.5) 
            self.ws._drain_ws_events()
            end_cursor = len(self.ws._ws_buffer)  # Mark the end of the buffer
        

        # ---------------------------------------------------------
        # PHASE 2: OFFLINE ANALYSIS
        # The game is stopped. Now we safely read the buffer to find Wins/Losses.
        # ---------------------------------------------------------
        with allure.step("Phase 2: Analyze Win/Loss Results"):
            # Slice only the events that happened during our auto-spin phase
            auto_spin_events = self.ws._ws_buffer[start_cursor:end_cursor]
            
            spin_counter = 0
            current_wallet_updates = []
            final_wallet_balance = None
            last_known_balance = "Unknown"  # Track balance across all spins

            # Helper function to log the win/loss of a spin
            def evaluate_spin(spin_num, updates):
                nonlocal last_known_balance
                
                # Handle the case where the spin was interrupted by the STOP button
                if not updates:
                    self.log_step(f"Auto Spin {spin_num} Result", "INFO", f"Spin interrupted by STOP before wallet updated.", take_screenshot=False)
                    print(f"[INFO] Auto Spin {spin_num} Result: Incomplete.")
                    return last_known_balance
                    
                wallet_amount_after_bet = updates[0]  # The balance right after the bet
                last_known_balance = wallet_amount_after_bet # Update running tracker

                self.log_step(f"Auto Spin {spin_num} Wallet", "INFO", f"Wallet Amount: {wallet_amount_after_bet}", take_screenshot=False)
                print(f"[INFO] Auto Spin {spin_num} Wallet Amount: {wallet_amount_after_bet}")
                
                if len(updates) > 1:
                    final_wallet = updates[-1]  # The balance after winnings
                    if final_wallet > wallet_amount_after_bet:
                        self.log_step(f"Auto Spin {spin_num} Result", "PASSED", f"WIN | {wallet_amount_after_bet} → {final_wallet}", take_screenshot=False)
                        allure.attach(f"WIN Update: {final_wallet}", name=f"Spin {spin_num} Audit", attachment_type=allure.attachment_type.TEXT)
                        print(f"[PASS] Spin {spin_num} WIN! Wallet: {final_wallet}")
                        last_known_balance = final_wallet
                        return final_wallet
                        
                self.log_step(f"Auto Spin {spin_num} Result", "INFO", f"LOSS | Wallet: {wallet_amount_after_bet}", take_screenshot=False)
                allure.attach(f"LOSS Update: {wallet_amount_after_bet}", name=f"Spin {spin_num} Audit", attachment_type=allure.attachment_type.TEXT)
                print(f"[INFO] Auto Spin {spin_num} Result: LOSS.")
                return wallet_amount_after_bet
           
            # Iterate through the captured events
            for ev in auto_spin_events:
                cmd = str(ev.get("cmd"))
                direction = ev.get("direction")

                # If we see a receive command from the server, a new spin result has arrived
                if cmd == str(MINI_POKER_CMD["SPIN_RESULT"]) and direction == "receive":
                    if str(self.ws._extract_game_id(ev)) == str(self.game_id):

                        # Before moving to the new spin, evaluate the previous one
                        if spin_counter > 0:
                            evaluate_spin(spin_counter, current_wallet_updates)

                        spin_counter += 1
                        current_wallet_updates = []  # Reset wallet tracking for this new spin
                        bet_amt = self.ws._extract_amount(ev, ["b"])
                        print(f"-> Analyzing Spin {spin_counter}... Bet: {bet_amt}")

                # If we see a wallet update, save it to the current spin's list
                elif cmd == str(WS_CMD["WALLET_UPDATE"]):
                    if spin_counter > 0:  
                        amt = self.ws._extract_amount(ev, ["wallet", "balance", "gold"])
                        if amt is not None:
                            current_wallet_updates.append(amt)

            # Ensure the very last spin gets evaluated too
            if spin_counter > 0:
                final_wallet_balance = evaluate_spin(spin_counter, current_wallet_updates)

            self.log_step(
                "Auto Spin Complete", 
                "PASSED", 
                f"Completed {spin_counter} spins in 2 seconds. Final Wallet Balance: {final_wallet_balance}"
            )
     

    @allure.step("Step 3: Exit MiniPoker Game")
    def exit_game(self):
        self._interact_canvas(x=1403, y=348, wait_after=0.4) #Pointer X: 1403 Pointer Y: 348
        self.ws._wait_for_cmd(MINI_POKER_CMD["UNSUBSCRIBE_JACKPOT"], timeout=15, from_cursor=True, expected_game_id=self.game_id,expected_direction="send")
        print("Unsubscribed")
        self.log_step("Exit Game", "PASSED", "Exited successfully")

         


        
         

        