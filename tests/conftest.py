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
    driver.get(base_url)
    
    # Use configured URL or a fallback mock to ensure app loads
    gas_url = test_config.TEST_GAS_URL if test_config.TEST_GAS_URL else "http://mock-url"
    
    
    driver.execute_script(f"localStorage.setItem('oyo_gasUrl', '{gas_url}');")
    driver.execute_script("localStorage.setItem('oyo_userId', '');")
    driver.execute_script("localStorage.removeItem('oyo_accessToken');")
    driver.execute_script("localStorage.removeItem('oyo_refreshToken');")
    driver.refresh()

@pytest.fixture(scope="function")
def auto_login_mock(driver, base_url, setup_gas_url):
    """Injects mock fetch and tokens to simulate a logged-in state."""
    # This new approach avoids multiple refreshes which can cause timing issues.
    # 1. Go to a blank page to ensure a clean state.
    driver.get("about:blank")

    # 2. Inject a mock fetch script that will run on the *next* page load.
    mock_fetch_script = """
    window.fetch = async (url, options) => {
        console.log("Mock fetch called for", url);
        // Handle validation
        if (options && options.body && options.body.includes('validate')) {
            return {
                ok: true,
                status: 200,
                json: async () => ({ valid: true, userId: 'testuser_mock', success: true })
            };
        }
        // Handle cloud sync/load (return success to avoid errors)
        if (options && options.body && (options.body.includes('action=load') || options.body.includes('action=save'))) {
             return {
                ok: true,
                status: 200,
                json: async () => ({ success: true, version: 1, data: {} })
            };
        }
        // Handle other requests
        return {
            ok: true,
            status: 200,
            json: async () => ({ success: true, valid: true })
        };
    };
    """
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": mock_fetch_script})

    # 3. Set all necessary localStorage items BEFORE navigating to the app.
    gas_url = test_config.TEST_GAS_URL if test_config.TEST_GAS_URL else "http://mock-url"
    driver.execute_script(f"localStorage.setItem('oyo_gasUrl', '{gas_url}');")
    driver.execute_script("localStorage.setItem('oyo_userId', 'testuser_mock');")
    driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_token');")
    driver.execute_script("localStorage.setItem('oyo_refreshToken', 'mock_refresh_token');")

    # 4. Now, navigate to the actual application URL.
    # The browser will load the page, and our injected script and localStorage will be used.
    print("\nDEBUG: auto_login_mock - All mocks and tokens set. Navigating to the app...")
    driver.get(base_url)

    # 5. Wait for the app to be fully interactive.
    print("DEBUG: auto_login_mock - Waiting for UI to be clickable...")
    wait = WebDriverWait(driver, 20)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link")))
    print("DEBUG: auto_login_mock - UI is ready. Fixture setup complete.")

def wait_for_overlays_to_disappear(driver, timeout=5):
    """
    Waits for all common overlays to become invisible.
    If an overlay doesn't disappear, it will raise a TimeoutException.
    """
    overlays = ["loading-overlay", "login-modal", "sync-modal"]
    # Use a shorter wait time for each check, as we expect them to be gone quickly.
    wait = WebDriverWait(driver, 1) # Short wait for the check
    for overlay_id in overlays:
        try:
            # Check if the overlay is present and visible.
            # If it is, wait for it to become invisible.
            overlay = driver.find_element(By.ID, overlay_id)
            if overlay.is_displayed():
                print(f"DEBUG: Overlay '{overlay_id}' is visible, waiting for it to disappear...")
                WebDriverWait(driver, timeout).until(EC.invisibility_of_element_located((By.ID, overlay_id)))
                print(f"DEBUG: Overlay '{overlay_id}' has disappeared.")
        except EC.NoSuchElementException:
            # If the element is not found, it's already gone, which is good.
            pass

def robust_click(driver, by, value, timeout=20):
    """
    A robust click function that waits for an element to be clickable and
    handles StaleElementReferenceException by retrying.
    Uses JavaScript click as a fallback.
    """
    # Use a slightly shorter wait for individual steps to provide more granular feedback
    wait = WebDriverWait(driver, timeout) 
    attempts = 3
    for i in range(attempts):
        try:
            print(f"DEBUG: robust_click - Attempt {i+1}/{attempts} for element ({by}, {value})")
            # Wait for the element to be present and visible first
            print(f"DEBUG: robust_click - Waiting for element to be visible...")
            element = wait.until(EC.visibility_of_element_located((by, value)))
            print(f"DEBUG: robust_click - Element is visible. Waiting for it to be clickable...")
            # Then wait for it to be clickable
            wait.until(EC.element_to_be_clickable((by, value)))
            print(f"DEBUG: robust_click - Element is clickable. Attempting standard click...")
            # Try a standard click first
            element.click()
            print(f"DEBUG: robust_click - Standard click successful.")
            return # Success
        except EC.StaleElementReferenceException as e:
            print(f"DEBUG: robust_click - StaleElementReferenceException caught, retrying... Details: {e}")
            time.sleep(0.5) # Brief pause before retrying
        except EC.ElementClickInterceptedException as e:
            print(f"DEBUG: robust_click - ElementClickInterceptedException caught, trying JS click. Details: {e}")
            driver.execute_script("arguments[0].click();", element)
            print(f"DEBUG: robust_click - JS click successful.")
            return # Success
    raise Exception(f"Failed to click element ({by}, {value}) after {attempts} attempts.")

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
        wait.until(EC.element_to_be_clickable((By.ID, "login-button"))).click()
        
        # Wait for success message or modal close
        # This part depends on actual backend response.
        # If backend is not available, this might timeout.
        # We'll assume for now that the user has set up a valid test environment.
        wait.until(EC.invisibility_of_element_located((By.ID, "login-modal")))
    except Exception as e:
        print(f"Login failed or timed out: {e}")
