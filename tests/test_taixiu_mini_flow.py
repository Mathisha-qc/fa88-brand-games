# tests/test_taixiu_mini_flow.py
import allure
import time
from tests.login_popup_flow import login_and_clear_popups
from pages.taixiu_mini_game_page import TaiXiuMiniGamePage
from reports.custom_report import report


@allure.feature("Tai Xiu Mini")
@allure.story("Open game entry flow")

def test_taixiu_mini_open_flow(driver):
    report.game_name = "TaiXiu Mini"
    wallet_before = login_and_clear_popups(driver)
    
    tx_page = TaiXiuMiniGamePage(driver)
    with allure.step("Open Tai Xiu mini game and validate one round state"):
        tx_page.open_taixiu_mini_game()

    
        tx_page.play_and_validate_flow(
            wallet_before=wallet_before,
            chip_amount=1000.0,
        )

        time.sleep(3)
        tx_page.exit_game()
