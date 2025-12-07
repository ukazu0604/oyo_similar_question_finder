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

def test_login_success(driver, base_url, wait):
    """Test successful login."""
    driver.get(base_url)
    
    # Open login modal
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
    driver.find_element(By.ID, "login-button").click()
    
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

def test_login_failure(driver, base_url, wait):
    """Test login failure."""
    driver.get(base_url)
    
    wait.until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "login-modal")))
    
    mock_fetch_error(driver, "Invalid credentials")
    
    driver.find_element(By.ID, "login-user-id").send_keys("wronguser")
    driver.find_element(By.ID, "login-password").send_keys("wrongpass")
    driver.find_element(By.ID, "login-button").click()
    
    status = wait.until(lambda d: d.find_element(By.ID, "auth-status").text)
    assert "Invalid credentials" in status

def test_logout(driver, base_url, wait):
    """Test logout."""
    driver.get(base_url)
    
    # Manually set token to simulate logged in state
    driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_token');")
    driver.execute_script("localStorage.setItem('oyo_userId', 'testuser');")
    driver.refresh()
    
    # Click auth button (now logout)
    # Handle confirm dialog
    driver.execute_script("window.confirm = () => true;")
    
    wait.until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()
    
    # Verify token removed
    wait.until(lambda d: d.execute_script("return localStorage.getItem('oyo_accessToken');") is None)

def test_manual_sync_upload(driver, base_url, wait):
    """Test manual upload button."""
    driver.get(base_url)
    
    # Login first
    driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_token');")
    driver.execute_script("localStorage.setItem('oyo_userId', 'testuser');")
    driver.execute_script("localStorage.setItem('oyo_gasUrl', 'http://mock-url');")
    driver.refresh()
    
    # Open sync modal
    wait.until(EC.element_to_be_clickable((By.ID, "sync-settings-button"))).click()
    
    # Mock save response
    mock_response = {
        "success": True,
        "version": 123
    }
    mock_fetch_success(driver, mock_response)
    
    # Click upload
    wait.until(EC.element_to_be_clickable((By.ID, "manual-sync-upload"))).click()
    
    # Verify status message
    status = wait.until(lambda d: d.find_element(By.ID, "sync-status").text)
    assert "アップロード完了" in status
