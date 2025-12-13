import pytest
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def mock_fetch_success(driver, response_data):
    """Mocks window.fetch to return a successful JSON response."""
    driver.execute_script("""
        window.fetch = async (url, options) => {
            console.log("Mock fetch called for", url);
            return {
                ok: true,
                status: 200,
                json: async () => (%s)
            };
        };
    """ % json.dumps(response_data))

def mock_fetch_error(driver, error_message):
    """Mocks window.fetch to return an error."""
    driver.execute_script("""
        window.fetch = async (url, options) => {
            console.log("Mock fetch error called for", url);
            return {
                ok: true,
                status: 200,
                json: async () => ({ error: '%s' })
            };
        };
    """ % error_message)

def test_login_success(driver, base_url, wait, setup_gas_url):
    """Test successful login."""
    # The setup_gas_url fixture already navigates to the base_url.
    
    # Open login modal
    # Ensure GAS URL is set to avoid blocking modal
    driver.execute_script("if (!localStorage.getItem('oyo_gasUrl')) { localStorage.setItem('oyo_gasUrl', 'http://mock-url'); localStorage.setItem('oyo_userId', ''); window.location.reload(); }")
    
    # Check if login modal is already open (auto-open behavior)
    try:
        modal = driver.find_element(By.ID, "login-modal")
        if not modal.is_displayed():
            wait.until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()
    except:
        wait.until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()

    wait.until(EC.visibility_of_element_located((By.ID, "login-modal")))
    
    # Mock successful login response
    mock_response = {
        "success": True,
        "accessToken": "mock_access_token",
        "refreshToken": "mock_refresh_token",
        "userId": "testuser_mock"
    }
    mock_fetch_success(driver, mock_response)
    
    # Fill and submit
    driver.find_element(By.ID, "login-user-id").send_keys("testuser")
    driver.find_element(By.ID, "login-password").send_keys("password")
    
    # Mock window.location.reload to prevent page reload from clearing our mocks
    driver.execute_script("window.location.reload = function() { console.log('Reload blocked by test'); };")
    
    wait.until(EC.element_to_be_clickable((By.ID, "login-button"))).click()
    
    # Verify success message or modal close
    # The app reloads on success, so we check for that or the notification
    # Since reload happens, the mock might be lost, but the localStorage should be set.
    
    # Wait for reload or UI update. 
    # Note: reload clears the mock.
    # We can check if localStorage has the token.
    
    def check_token(d):
        return d.execute_script("return localStorage.getItem('oyo_accessToken');") == "mock_access_token"
    
    wait.until(check_token)
    
    # After reload, check user display
    # We need to wait for the page to reload and app to init
    wait.until(EC.presence_of_element_located((By.ID, "current-user-display")))
    # Since we mocked the login call, the reload happens. 
    # But on reload, `validate` is called. If we don't mock that, it might fail if GAS URL is not set or real.
    # However, if TEST_GAS_URL is not set, it might fail.
    # But the test should verify that the login *action* succeeded.

def test_login_failure(driver, base_url, wait, setup_gas_url):
    """Test login failure."""
    # The setup_gas_url fixture already navigates to the base_url.
    
    # Check if login modal is already open (auto-open behavior)
    try:
        modal = driver.find_element(By.ID, "login-modal")
        if not modal.is_displayed():
            wait.until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()
    except:
        wait.until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()

    wait.until(EC.visibility_of_element_located((By.ID, "login-modal")))
    
    mock_fetch_error(driver, "Invalid credentials")
    
    driver.find_element(By.ID, "login-user-id").send_keys("wronguser")
    driver.find_element(By.ID, "login-password").send_keys("wrongpass")
    wait.until(EC.element_to_be_clickable((By.ID, "login-button"))).click()
    
    status = wait.until(lambda d: d.find_element(By.ID, "auth-status").text)
    assert "Invalid credentials" in status

def test_logout(driver, base_url, wait, setup_gas_url):
    """Test logout."""
    # The setup_gas_url fixture already navigates to the base_url.
    # App starts with login modal open (because no token). Close it first.
    try:
        driver.find_element(By.ID, "close-login-modal").click()
        time.sleep(0.5) # Wait for animation
    except:
        pass

    # Manually set token to simulate logged in state without refresh (refresh clears mocks/state)
    driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_token');")
    driver.execute_script("localStorage.setItem('oyo_userId', 'testuser');")
    # Update internal storage object if exposed, or trigger storage event?
    # Since we can't easily trigger the reactivity from outside without refresh, 
    # and refresh kills the mock... 
    # Actually, verify if auth-button click reads from localStorage directly?
    # app.js: if (storage.accessToken) ... 
    # storage.js reads from localStorage on property access. So setting localStorage is enough!
    
    # Click auth button (now logout)
    # Handle confirm dialog
    driver.execute_script("window.confirm = () => true;")
    
    # Wait for any notification to disappear
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "notification-message")))

    wait.until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()
    
    # Verify token removed
    wait.until(lambda d: d.execute_script("return localStorage.getItem('oyo_accessToken');") is None)

def test_manual_sync_upload(driver, base_url, wait, setup_gas_url):
    """Test manual upload button."""
    # The setup_gas_url fixture already navigates to the base_url.
    
    # Close default login modal
    try:
        driver.find_element(By.ID, "close-login-modal").click()
        time.sleep(0.5)
    except:
        pass

    # Login first
    driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_token');")
    driver.execute_script("localStorage.setItem('oyo_userId', 'testuser');")
    driver.execute_script("localStorage.setItem('oyo_gasUrl', 'http://mock-url');")
    # No refresh, just state injection
    
    # Open sync modal
    wait.until(EC.element_to_be_clickable((By.ID, "sync-settings-button"))).click()
    
    # Mock save response
    mock_response = {
        "success": True,
        "version": 123
    }
    mock_fetch_success(driver, mock_response)
    
    # Wait for any notification to disappear (e.g. "GAS URL..." or login prompts)
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "notification-message")))
    wait.until(EC.element_to_be_clickable((By.ID, "manual-sync-upload"))).click()
    
    # Verify status message
    status = wait.until(lambda d: d.find_element(By.ID, "sync-status").text)
    assert "アップロード完了" in status
