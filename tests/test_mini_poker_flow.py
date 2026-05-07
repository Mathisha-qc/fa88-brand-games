# tests/test_mini_poker_flow.py
import allure
import time
from tests.login_popup_flow import login_and_clear_popups
from pages.mini_poker_game_page import MiniPokerGamePage
from reports.custom_report import report


@allure.feature("MiniPoker")
@allure.story("Open game entry flow")

def test_mini_poker_open_flow(driver):
    report.game_name = "MiniPoker (Game_id-199)"
    wallet_before = login_and_clear_popups(driver)
    
    mp_page = MiniPokerGamePage(driver)
    with allure.step("Open MiniPoker game and validate one round state"):
        mp_page.open_mini_poker_game()

    
        mp_page.play_and_validate_flow(
            wallet_before=wallet_before,
            chip_amount=100.0,
        )

        time.sleep(3)
        mp_page.exit_game()
