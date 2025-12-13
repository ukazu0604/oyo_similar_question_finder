import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def test_favorite_persistence(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test that favorites are persisted after reload."""
    # The auto_login_mock fixture handles login and initial page load.
    # It also ensures the UI is ready and clickable.
    print("\n--- test_favorite_persistence: START ---")
    print("--- test_favorite_persistence: Waiting for category link to be clickable and clicking it...")
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    
    print("--- test_favorite_persistence: Waiting for detail view to be visible...")
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    print("--- test_favorite_persistence: Detail view is visible.")

    print("--- test_favorite_persistence: Waiting for read-only mode to be disabled...")
    wait.until(lambda d: d.execute_script("return not window.isReadOnlyMode"))
    print("--- test_favorite_persistence: Read-only mode is disabled.")
    
    # Find a star and click it
    print("--- test_favorite_persistence: Finding star icon...")
    star = driver.find_element(By.CLASS_NAME, "star-icon")
    problem_id = star.get_attribute("data-problem-id")
    
    # Ensure it's not active initially (or handle if it is)
    if "active" in star.get_attribute("class"):
        print(f"--- test_favorite_persistence: Star for problem {problem_id} is already active, deactivating it first...")
        driver.execute_script("arguments[0].click();", star)
        print("--- test_favorite_persistence: Waiting for star to become inactive...")
        wait.until(lambda d: "active" not in star.get_attribute("class"))
    
    print(f"--- test_favorite_persistence: Clicking star for problem {problem_id}...")
    driver.execute_script("arguments[0].click();", star)
    print("--- test_favorite_persistence: Waiting for star to become active...")
    wait.until(lambda d: "active" in star.get_attribute("class"))
    print(f"--- test_favorite_persistence: Star for problem {problem_id} marked as favorite.")
    
    # Reload
    print("--- test_favorite_persistence: Reloading page...")
    driver.refresh()
    print("--- test_favorite_persistence: Waiting for detail view to be visible after reload...")
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    print("--- test_favorite_persistence: Page reloaded, detail view is visible.")
    
    # Find the same star
    print(f"--- test_favorite_persistence: Verifying star for problem {problem_id} is still active...")
    star_after = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".star-icon[data-problem-id='{problem_id}']")))
    assert "active" in star_after.get_attribute("class")
    print("--- test_favorite_persistence: SUCCESS ---")

def test_favorite_filter(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test filtering by favorites."""
    print("\n--- test_favorite_filter: START ---")
    # The auto_login_mock fixture handles login and initial page load.

    print("--- test_favorite_filter: Waiting for category link to be clickable and clicking it...")
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    print("--- test_favorite_filter: Waiting for detail view to be visible...")
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    print("--- test_favorite_filter: Waiting for read-only mode to be disabled...")
    wait.until(lambda d: d.execute_script("return not window.isReadOnlyMode"))
    print("--- test_favorite_filter: Read-only mode is disabled.")
    
    # Mark first item as favorite
    print("--- test_favorite_filter: Finding star icons...")
    stars = driver.find_elements(By.CLASS_NAME, "star-icon")
    if not stars:
        pytest.skip("No problems found")
        
    first_star = stars[0]
    if "active" not in first_star.get_attribute("class"):
        driver.execute_script("arguments[0].click();", first_star)
        print("--- test_favorite_filter: Waiting for the first star to become active...")
        wait.until(lambda d: "active" in first_star.get_attribute("class"))
    
    # Enable filter
    print("--- test_favorite_filter: Clicking 'show-favorites-only' checkbox...")
    filter_chk = driver.find_element(By.ID, "show-favorites-only")
    driver.execute_script("arguments[0].click();", filter_chk)
    
    # --- デバッグのためのprint文を追加 ---
    print(f"\nDEBUG: Favorited problem ID: {first_star.get_attribute('data-problem-id')}")
    
    print("--- test_favorite_filter: Waiting for the list to be filtered...")
    
    # Verify only favorites are shown
    # Wait for list update. Instead of staleness_of, wait for the number of items to change
    # or for a specific condition to be met.
    def favorites_are_filtered(d):
        # Find all visible problem cards
        visible_cards = d.find_elements(By.CSS_SELECTOR, ".problem-card:not([style*='display: none'])")
        if not visible_cards:
            return False # List might be empty during transition
        # Check if all visible cards have an active star
        for card in visible_cards:
            star = card.find_element(By.CLASS_NAME, "star-icon")
            if "active" not in star.get_attribute("class"):
                return False
        return True

    wait.until(favorites_are_filtered)
    print("--- test_favorite_filter: SUCCESS ---")
