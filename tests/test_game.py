import time
import allure
from pages.login_page import LoginPage
from pages.popup_handler import PopupHandler
from pages.game_page import GamePage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@allure.suite("HitClub Production Suite")
@allure.feature("End-to-End Game Flow")
class TestHitClub:

    @allure.title("Case #1: User Authentication & Captcha")
    @allure.description("Validates the canvas login process and captcha handling.")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_01_login(self, driver):
        # 1. Load the site
        driver.get("https://v.hitclub.sc/")
        login_pg = LoginPage(driver)

        with allure.step("Wait for Game Engine"):
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))
            time.sleep(10)

        with allure.step("Input Credentials"):
            login_pg.click_login_menu()
            time.sleep(2) 
            login_pg.enter_user("Mathisha1")
            login_pg.enter_pass("678910")

        with allure.step("Manual Captcha Solver"):
            print("\n[!] ACTION REQUIRED: Solve Captcha!")
            time.sleep(20) # 20s for manual solve
            login_pg.click_final_submit()
            time.sleep(20)

        with allure.step("Clear Lobby Popups"):
            popup = PopupHandler(driver)
            popup.clear_all_whenever(timeout=30)

    @allure.title("Case #2: Xoc Dia - Game Flow")
    @allure.description("Validates navigation to Live section, WebSocket betting signals and navigation to lobby(Exit Game).")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_02_betting_flow(self, driver):
        game = GamePage(driver)
        
        # This will now show as a separate 'bubble' in Allure
        game.open_live_section()
        
        # Internal steps and WS attachments are handled inside this method
        game.select_game_and_validate_ws_flow(
            chip_amount=1000.0,
            chip_1k_xy=(769, 881),   
            bet_area_xy=(668, 506),
        )

        # Exit from game
        game.exit_game()