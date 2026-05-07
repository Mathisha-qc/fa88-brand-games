import allure
import time
from tests.login_popup_flow import login_and_clear_popups
from pages.tren_duoi_mini_game_page import TrenDuoiMiniGamePage
from reports.custom_report import report


@allure.feature("Tren-Duoi")
@allure.story("Open game entry flow")

def test_trenduoi_mini_open_flow(driver):
    report.game_name = "Tren-Duoi Mini"
    wallet_before = login_and_clear_popups(driver)
    
    updown_page = TrenDuoiMiniGamePage(driver)
    with allure.step("Open Tren-Duoi mini game and validate one round state"):
        updown_page.open_trenduoi_mini_game()

    
        updown_page.play_until_win_1503(
            wallet_before=wallet_before,
            chip_amount=1000.0,
            max_attempts=20
        )

        time.sleep(3)
        updown_page.exit_game()
