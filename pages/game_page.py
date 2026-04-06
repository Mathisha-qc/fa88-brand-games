import json
import re
import time
import allure
from pages.base_page import BasePage
from utils.ws_commands import WS_CMD

@allure.feature("Game Mechanics")
@allure.story("Xoc Dia Betting Flow")
class GamePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self._ws_buffer = []
        self._cursor = 0  # pointer for "next event" reads

    @allure.step("Step 1: Navigate to Live Game Section")
    def open_live_section(self):
        print("[INFO] Clicking 'Live' tab...")
        self._interact_canvas(x=1379, y=206, wait_after=2.0)

    def _extract_cmd_from_payload(self, payload):
        try:
            data = json.loads(payload)

            if isinstance(data, dict) and "cmd" in data:
                return str(data["cmd"]), data

            if isinstance(data, dict) and isinstance(data.get("data"), dict) and "cmd" in data["data"]:
                return str(data["data"]["cmd"]), data

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "cmd" in item:
                        return str(item["cmd"]), data
        except Exception:
            data = None

        m = re.search(r'"cmd"\s*:\s*"?(\d+)"?', payload)
        if m:
            return m.group(1), data

        return None, data

    def _drain_ws_events(self):
        try:
            logs = self.driver.get_log("performance")
            for entry in logs:
                msg = json.loads(entry["message"]).get("message", {})
                if msg.get("method") not in (
                    "Network.webSocketFrameReceived",
                    "Network.webSocketFrameSent",
                ):
                    continue

                payload = msg.get("params", {}).get("response", {}).get("payloadData", "")
                if not payload:
                    continue

                cmd, parsed = self._extract_cmd_from_payload(payload)
                if cmd:
                    self._ws_buffer.append({"cmd": cmd, "data": parsed, "raw": payload})
        except Exception:
            pass

    def _wait_for_cmd(self, cmd, timeout=20, from_cursor=False):
        target = str(cmd)
        # Dynamic step naming for the report
        with allure.step(f"WS Scan: Waiting for CMD {target}"):
            end = time.time() + timeout
            while time.time() < end:
                self._drain_ws_events()
                start_idx = self._cursor if from_cursor else 0
                for i in range(start_idx, len(self._ws_buffer)):
                    ev = self._ws_buffer[i]
                    if ev["cmd"] == target:
                        self._cursor = i + 1
                        # Attach the found JSON to the Allure report for auditing
                        allure.attach(
                            json.dumps(ev, indent=2), 
                            name=f"Found CMD {target}", 
                            attachment_type=allure.attachment_type.JSON
                        )
                        return ev
                time.sleep(0.3)

            seen = [e["cmd"] for e in self._ws_buffer[-30:]]
            error_msg = f"[FAIL] WS cmd {target} not found within {timeout}s. Last seen: {seen}"
            allure.attach(str(seen), name="Last 30 WS Commands Received", attachment_type=allure.attachment_type.TEXT)
            assert False, error_msg

    def _extract_amount(self, ev, keys):
        data = ev.get("data")

        if isinstance(data, dict):
            for k in keys:
                if k in data:
                    try:
                        return float(data[k])
                    except Exception:
                        pass

            nested = data.get("data")
            if isinstance(nested, dict):
                for k in keys:
                    if k in nested:
                        try:
                            return float(nested[k])
                        except Exception:
                            pass

            as_obj = data.get("As")
            if isinstance(as_obj, dict) and "gold" in as_obj:
                try:
                    return float(as_obj["gold"])
                except Exception:
                    pass

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for k in keys:
                        if k in item:
                            try:
                                return float(item[k])
                            except Exception:
                                pass
                    as_obj = item.get("As")
                    if isinstance(as_obj, dict) and "gold" in as_obj:
                        try:
                            return float(as_obj["gold"])
                        except Exception:
                            pass

        raw = ev.get("raw", "")
        m = re.search(r'"gold"\s*:\s*([0-9]+(?:\.[0-9]+)?)', raw)
        if m:
            return float(m.group(1))

        for k in keys:
            m = re.search(rf'"{k}"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?', raw)
            if m:
                return float(m.group(1))

        return None
    
    @allure.step("Step 2 Main Flow: Join Game, Place Bet, and Verify Wallet")
    def select_game_and_validate_ws_flow(
        self,
        chip_amount=1000.0,
        chip_1k_xy=(762, 889),
        bet_area_xy=(1268, 523),           #(1279, 644), CHAN -> X: 668 Pointer Y: 506 Pointer; LE -> X: 1268 Pointer Y: 523
    ):
     with allure.step("1. Enter Game and Validate Subscriptions"):
        print("[INFO] Selecting game...")
        self._interact_canvas(x=1051, y=571, wait_after=5.0)

        self._drain_ws_events()

        self._wait_for_cmd(WS_CMD["SUBSCRIBE"], timeout=2)
        print(f"[PASS] Subscribe cmd {WS_CMD['SUBSCRIBE']} detected.")

        self._wait_for_cmd(WS_CMD["JOIN_ROOM"], timeout=2)
        print(f"[PASS] Join room cmd {WS_CMD['JOIN_ROOM']} detected.")

     with allure.step("2. Wallet Balance Before Bet"):
        before_ev = self._wait_for_cmd(WS_CMD["WALLET_BEFORE"], timeout=10)
        wallet_before = self._extract_amount(
            before_ev, ["wallet", "balance", "money", "coin", "amount", "gold"]
        )
        allure.attach(f"Wallet Before: {wallet_before}", name="Audit", attachment_type=allure.attachment_type.TEXT)
        print(f"[INFO] Wallet before bet: {wallet_before}")

     with allure.step(f"3. Place Bet of {chip_amount}"):
        self._wait_for_cmd(WS_CMD["BET_START"], timeout=60)
        print(f"[PASS] Bet start cmd {WS_CMD['BET_START']} detected.")

        self._interact_canvas(x=chip_1k_xy[0], y=chip_1k_xy[1], wait_after=0.6)
        self._interact_canvas(x=bet_area_xy[0], y=bet_area_xy[1], wait_after=1.0)
        print("[INFO] Bet action done (1K -> place).")

        bet_ev = self._wait_for_cmd(WS_CMD["PLACE_BET"], timeout=10, from_cursor=True)
        bet_amount = self._extract_amount(bet_ev, ["betAmount", "amount", "chip", "value", "b"])
        assert bet_amount == float(chip_amount), (
            f"[FAIL] Bet amount mismatch. expected={chip_amount}, ws={bet_amount}"
        )
        print(f"[PASS] Place bet cmd {WS_CMD['PLACE_BET']} with amount={bet_amount}.")
        
     with allure.step("4. Verify Wallet Deduction After Bet"):
        # first wallet update after placing bet
        after_bet_ev = self._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=40, from_cursor=True)
        wallet_after_bet = self._extract_amount(
            after_bet_ev, ["wallet", "balance", "money", "coin", "amount", "gold"]
        )
        print(f"[INFO] Wallet after bet update: {wallet_after_bet}")

        assert wallet_before is not None, "[FAIL] Could not parse wallet_before."
        assert wallet_after_bet is not None, "[FAIL] Could not parse wallet_after_bet."

        expected_after_bet = wallet_before - float(chip_amount)
        allure.attach(f"Expected: {expected_after_bet}\nActual: {wallet_after_bet}", name="Math Results", attachment_type=allure.attachment_type.TEXT)
        assert abs(wallet_after_bet - expected_after_bet) <= 5, (
          f"[FAIL] wallet_after_bet mismatch. expected~{expected_after_bet}, actual={wallet_after_bet}"
        )
      
     with allure.step("5. Determine Round Result (Win/Loss)"):
        # optional final update: only assert if win; if lose, skip
        try:
           final_ev = self._wait_for_cmd(WS_CMD["WALLET_UPDATE"], timeout=40, from_cursor=True)
           wallet_final = self._extract_amount(
              final_ev, ["wallet", "balance", "money", "coin", "amount", "gold"]
            )
        except AssertionError:
           wallet_final = None

        if wallet_final is None or wallet_final == wallet_after_bet:
             allure.dynamic.title("RESULT: LOSS")
             allure.attach(f"Wallet Update: {wallet_after_bet}", name="Audit", attachment_type=allure.attachment_type.TEXT)
             allure.attach(self.driver.get_screenshot_as_png(), name="Loss_Moment", attachment_type=allure.attachment_type.PNG)
             print("[INFO] LOSE and no extra wallet update. Skipping win update validation.")
        elif wallet_final > wallet_after_bet:
          allure.dynamic.title("RESULT: WIN")
          allure.attach(f"Wallet Update: {wallet_final}", name="Audit", attachment_type=allure.attachment_type.TEXT)
          allure.attach(self.driver.get_screenshot_as_png(), name="Win_Moment", attachment_type=allure.attachment_type.PNG)
          print(f"[PASS] WIN detected. Wallet updated: {wallet_after_bet} -> {wallet_final}")
        else:
          assert False, (
            f"[FAIL] Invalid wallet flow. final={wallet_final} < after_bet={wallet_after_bet}"
            )
          
        # round-end validation (must happen for one completed round)
        self._wait_for_cmd(WS_CMD["END_GAME"], timeout=30, from_cursor=True)
        print(f"[PASS] Round end cmd {WS_CMD['END_GAME']} detected.")

    @allure.step("Step 3: Exit from The Game")
    def exit_game(self):
        print("[INFO] Clicking 'Back' tab")
        self._interact_canvas(x=77, y=214, wait_after=0.4) #X: 77 Pointer Y: 214
        print("[INFO] Clicking 'Exit' button")
        self._interact_canvas(x=187, y=330, wait_after=0.5) # X: 187 Pointer Y: 330

        # leave-room validation 
        self._wait_for_cmd(WS_CMD["LEAVE_ROOM"], timeout=10, from_cursor=True)
        print(f"[PASS] Leave room cmd {WS_CMD['LEAVE_ROOM']} detected.")

        # unsubcribe 
        self._wait_for_cmd(WS_CMD["UNSUBSCRIBE"], timeout=10, from_cursor=True)
        print(f"[PASS] Unsubscribe cmd {WS_CMD['UNSUBCRIBE']} detected")


