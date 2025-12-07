import pytest
import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import test_config

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture(scope="session")
def driver():
    options = Options()
    if test_config.HEADLESS_MODE:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def wait(driver):
    return WebDriverWait(driver, 10)

@pytest.fixture(scope="session")
def base_url():
    return test_config.BASE_URL

@pytest.fixture(scope="function")
def setup_gas_url(driver, base_url):
    """Sets the GAS URL in localStorage if configured."""
    if test_config.TEST_GAS_URL:
        driver.get(base_url)
        # Set config and reload
        driver.execute_script(f"localStorage.setItem('gas_config', JSON.stringify({{url: '{test_config.TEST_GAS_URL}', userId: null}}));")
        driver.refresh()
    else:
        # If no URL is set, the app might show the sync modal.
        # We can try to dismiss it or let the test handle it.
        pass

@pytest.fixture(scope="function")
def login_user(driver, base_url, wait, setup_gas_url):
    """Logs in a test user."""
    driver.get(base_url)
    
    # Check if already logged in
    try:
        user_display = driver.find_element(By.ID, "current-user-display")
        if user_display.text and "User:" in user_display.text:
            return
    except:
        pass

    # Open login modal
    try:
        auth_btn = wait.until(EC.element_to_be_clickable((By.ID, "auth-button")))
        auth_btn.click()
        
        # Fill credentials
        wait.until(EC.visibility_of_element_located((By.ID, "login-user-id"))).send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        
        # Click login
        driver.find_element(By.ID, "login-button").click()
        
        # Wait for success message or modal close
        # This part depends on actual backend response.
        # If backend is not available, this might timeout.
        # We'll assume for now that the user has set up a valid test environment.
        wait.until(EC.invisibility_of_element_located((By.ID, "login-modal")))
    except Exception as e:
        print(f"Login failed or timed out: {e}")
