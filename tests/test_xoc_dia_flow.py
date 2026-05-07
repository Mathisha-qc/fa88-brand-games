import allure
from pages.xoc_dia_game_page import XocDiaGamePage
from tests.login_popup_flow import login_and_clear_popups


@allure.suite("HitClub Production Suite")
@allure.feature("End-to-End Game Flow")
class TestXocDiaFlow:
    @allure.title("Case #2: Xoc Dia - Game Flow")
    @allure.description(
        "Validates navigation to Live section, WebSocket betting signals and navigation to lobby(Exit Game)."
    )
    @allure.severity(allure.severity_level.BLOCKER)
    def test_betting_flow(self, driver):
        login_and_clear_popups(driver, username="Mathisha1", password="678910")

        game = XocDiaGamePage(driver)
        game.open_live_section()
        game.select_game_and_validate_ws_flow(
            chip_amount=1000.0,
            chip_1k_xy=(769, 881),
            bet_area_xy=(668, 506),
        )
        game.exit_game()




