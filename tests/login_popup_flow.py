import time
import allure
from pages.login_page import LoginPage
from pages.popup_handler import PopupHandler
from core.ws_engine import WSEngine
from utils.ws_commands import WS_CMD
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@allure.step("Login and clear popups")
def login_and_clear_popups(driver, username="mathisha1", password="678910", captcha="ma"):
    login_pg = LoginPage(driver)

    ws = WSEngine(driver, login_pg.log_step)
    
    with allure.step("Open website"):
      driver.get("https://v.hitclub.sc/")
      
      

    with allure.step("Wait for Game Engine"):
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )

        time.sleep(5)

        driver.refresh()

        time.sleep(20)

        login_pg.step(
        "Landing Page Loaded",
        "PASSED",
        "Game canvas loaded successfully"
        )

    with allure.step("Input Credentials"):
        login_pg.click_login_menu()
        time.sleep(2)
        login_pg.enter_user(username)
        login_pg.enter_pass(password)
        login_pg.enter_cap(captcha)
        login_pg.click_final_submit()

    time.sleep(20)
    with allure.step("Fetch Wallet (CMD 100)"):
        ev = ws._wait_for_cmd(WS_CMD["USER_INFO"], timeout=30)

        wallet_before = ws._extract_amount(
            ev,
            ["wallet", "balance", "gold"]
        )

        assert wallet_before is not None, "[FAIL] wallet_before not found"

        allure.attach(
            str(wallet_before),
            name="Wallet Before",
            attachment_type=allure.attachment_type.TEXT
        )
        login_pg.step(
          "Login Success (CMD 100)",
          "PASSED",
          "Entered lobby"
        )


        print(f"[INFO] Wallet before: {wallet_before}")


    time.sleep(20)
    with allure.step("Clear Lobby Popups"):
        popup = PopupHandler(driver)
        popup.clear_all_whenever(timeout=30)

        login_pg.step(
          "Popups Cleared",
          "PASSED",
          "All popups handled successfully"
        )

    return wallet_before