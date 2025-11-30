import pytest
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000/"

def wait_for_notification(driver, message_part):
    """Wait for a notification containing specific text."""
    WebDriverWait(driver, 10).until(
        lambda d: any(message_part in n.text for n in d.find_elements(By.CLASS_NAME, "notification"))
    )

def mock_gas_api(driver):
    """
    Injects a mock fetch function to intercept GAS API calls.
    This allows testing without a real GAS backend.
    """
    mock_script = """
    window.originalFetch = window.fetch;
    window.mockGasResponse = {
        'login': { success: true, accessToken: 'mock_access_token', refreshToken: 'mock_refresh_token', userId: 'testuser' },
        'register': { success: true, message: 'User registered successfully' },
        'save': { success: true, version: 1 },
        'load': { success: true, data: { 'test_key': 'test_value' }, version: 1 },
        'validate': { valid: true, userId: 'testuser' },
        'refresh': { success: true, accessToken: 'new_mock_access_token', userId: 'testuser' }
    };

    window.fetch = async (url, options) => {
        if (url.includes('script.google.com')) {
            console.log('Mocking GAS request:', url, options);
            const body = JSON.parse(options.body);
            const action = body.action;
            
            // Simulate network delay
            await new Promise(r => setTimeout(r, 100));

            if (window.mockGasResponse[action]) {
                const response = window.mockGasResponse[action];
                // Simulate error if configured
                if (response.error) {
                    return {
                        ok: true,
                        json: async () => ({ error: response.error })
                    };
                }
                return {
                    ok: true,
                    json: async () => response
                };
            }
            return { ok: true, json: async () => ({ error: 'Unknown action' }) };
        }
        return window.originalFetch(url, options);
    };
    """
    driver.execute_script(mock_script)

class TestAuthAndSync:

    def test_login_flow(self, driver, page_load_waiter):
        """
        Test the login flow: open modal, enter credentials, login, verify success.
        """
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)

        # Open Login Modal
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))

        # Enter Credentials
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")

        # Click Login
        driver.find_element(By.ID, "login-button").click()

        # Wait for success notification or reload
        # Since login reloads the page, we need to handle that.
        # However, our mock might be lost on reload. 
        # But the app saves tokens to localStorage BEFORE reload.
        # So we can check localStorage after reload.
        
        # Wait for the "Login successful" notification or status update
        WebDriverWait(driver, 5).until(
            lambda d: "ログイン成功" in d.find_element(By.ID, "auth-status").text
        )

        # Wait for page reload (simulated by checking if modal is gone or user display updates)
        # Actually, the app does `location.reload()` after 1s.
        time.sleep(1.5) 
        page_load_waiter()

        # Verify logged in state
        user_display = driver.find_element(By.ID, "current-user-display").text
        assert "User: testuser" in user_display

        # Verify tokens in localStorage
        tokens = driver.execute_script("return {access: localStorage.getItem('oyo_accessToken'), refresh: localStorage.getItem('oyo_refreshToken')}")
        assert tokens['access'] == 'mock_access_token'
        assert tokens['refresh'] == 'mock_refresh_token'

    def test_manual_sync(self, driver, page_load_waiter):
        """
        Test manual sync upload and download.
        Requires being logged in first.
        """
        # Pre-login state
        driver.get(BASE_URL)
        page_load_waiter()
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.execute_script("localStorage.setItem('oyo_refreshToken', 'mock_refresh_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        driver.refresh()
        page_load_waiter()
        mock_gas_api(driver)

        # Open Sync Modal
        driver.find_element(By.ID, "sync-settings-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "sync-modal")))

        # Test Upload
        driver.find_element(By.ID, "manual-sync-upload").click()
        WebDriverWait(driver, 5).until(
            lambda d: "アップロード完了" in d.find_element(By.ID, "sync-status").text
        )

        # Test Download
        driver.find_element(By.ID, "manual-sync-download").click()
        WebDriverWait(driver, 5).until(
            lambda d: "ダウンロード完了" in d.find_element(By.ID, "sync-status").text
        )

    def test_auto_sync_trigger(self, driver, page_load_waiter):
        """
        Test that auto-sync is triggered when data changes.
        """
        # Pre-login state
        driver.get(BASE_URL)
        page_load_waiter()
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        driver.refresh()
        page_load_waiter()
        mock_gas_api(driver)

        # Trigger a change (e.g., click a reaction button)
        # First, navigate to a detail view
        major_title = driver.find_element(By.CLASS_NAME, "major-title")
        major_title.click() # Open accordion
        time.sleep(0.5)
        driver.find_element(By.CSS_SELECTOR, ".middle-category-link").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "detail-view")))

        # Click "Oshi" button
        oshi_btn = driver.find_element(By.CSS_SELECTOR, ".reaction-button[data-reaction-type='oshi']")
        oshi_btn.click()

        # Wait for auto-sync notification (debounced 3s)
        # We need to wait at least 3 seconds + network time
        try:
            WebDriverWait(driver, 6).until(
                lambda d: any("自動保存しました" in n.text for n in d.find_elements(By.CLASS_NAME, "notification"))
            )
        except:
            pytest.fail("Auto-sync notification did not appear")

    def test_logout(self, driver, page_load_waiter):
        """
        Test logout functionality.
        """
        # Pre-login state
        driver.get(BASE_URL)
        page_load_waiter()
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.refresh()
        page_load_waiter()

        # Click Auth Button (which should be "Logout" or trigger logout confirmation)
        driver.find_element(By.ID, "auth-button").click()
        
        # Confirm logout
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()

        # Wait for reload
        time.sleep(1.5)
        page_load_waiter()

        # Verify logged out state
        user_display = driver.find_element(By.ID, "current-user-display").text
        assert user_display == ""
        
        # Verify tokens removed
        tokens = driver.execute_script("return {access: localStorage.getItem('oyo_accessToken')}")
        assert tokens['access'] is None
