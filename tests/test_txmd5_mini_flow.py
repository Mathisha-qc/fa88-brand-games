# tests/test_txmd5_mini_flow.py
import allure
import time


from tests.login_popup_flow import login_and_clear_popups
from pages.tx_md5_mini_game_page import TaiXiuMd5MiniGamePage
from reports.custom_report import report

@allure.feature("Tai Xiu Mini")
@allure.story("Open game entry flow")

def test_taixiu_md5_mini_open_flow(driver):
    report.game_name = "TaiXiu MD5 Mini"
    wallet_before = login_and_clear_popups(driver)

    txmd5_page = TaiXiuMd5MiniGamePage(driver)
    with allure.step("Open Tai Xiu MD5 mini game and validate one round state"):
        txmd5_page.open_taixiu_md5_mini_game()

    
        txmd5_page.play_and_validate_flow(
            wallet_before=wallet_before,
            chip_amount=1000.0,
        )

        time.sleep(3)
        txmd5_page.exit_game()

    
