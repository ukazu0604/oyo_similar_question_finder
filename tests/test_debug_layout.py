
import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_debug_page_state(driver, base_url, setup_gas_url, auto_login_mock):
    """Debugs the page state after login."""
    print("\nDEBUG: Starting debug test")
    
    # Check overlays
    try:
        loading = driver.find_element(By.ID, "loading-overlay")
        print(f"DEBUG: loading-overlay displayed: {loading.is_displayed()}, classes: {loading.get_attribute('class')}")
    except:
        print("DEBUG: loading-overlay element not found")
        
    try:
        login_modal = driver.find_element(By.ID, "login-modal")
        print(f"DEBUG: login-modal displayed: {login_modal.is_displayed()}")
    except:
        print("DEBUG: login-modal element not found")
        
    try:
        sync_modal = driver.find_element(By.ID, "sync-modal")
        print(f"DEBUG: sync-modal displayed: {sync_modal.is_displayed()}")
    except:
        print("DEBUG: sync-modal element not found")

    # Check category links
    links = driver.find_elements(By.CLASS_NAME, "middle-category-link")
    print(f"DEBUG: Found {len(links)} middle-category-links")
    if len(links) > 0:
        print(f"DEBUG: First link text: {links[0].text}")
        print(f"DEBUG: First link likely clickable? {links[0].is_displayed()} and enabled: {links[0].is_enabled()}")
    
    # Check user display
    try:
        user_display = driver.find_element(By.ID, "current-user-display")
        print(f"DEBUG: current-user-display text: '{user_display.text}'")
    except:
        print("DEBUG: current-user-display not found")

    assert len(links) > 0, "No category links found!"
