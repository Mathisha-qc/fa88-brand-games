import allure
from pages.base_page import BasePage

@allure.feature("Authentication")
@allure.story("Login via Canvas Interaction")
class LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver) # Connects to BasePage
        
    @allure.step("Step 1: Click the 'Login' menu button")
    def click_login_menu(self):
        self._interact_canvas(x=1104, y=750)

    @allure.step("Step 2: Enter username: '{username}'")
    def enter_user(self, username):
        self._interact_canvas(x=914, y=362, text=username)

    @allure.step("Step 3: Enter password")
    def enter_pass(self, password): 
        self._interact_canvas(x=986, y=489, text=password)
    
    @allure.step("Step 4: Enter captcha")
    def enter_cap(self): 
        self._interact_canvas(x=755, y=692)

    @allure.step("Step 4: Submit Login Credentials")
    def click_final_submit(self):
        self._interact_canvas(x=970, y=824, wait_after=4.0)
        