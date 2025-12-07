import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def test_favorite_persistence(driver, base_url, wait):
    """Test that favorites are persisted after reload."""
    driver.get(base_url)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    time.sleep(1)
    
    # Find a star and click it
    star = driver.find_element(By.CLASS_NAME, "star-icon")
    problem_id = star.get_attribute("data-problem-id")
    
    # Ensure it's not active initially (or handle if it is)
    if "active" in star.get_attribute("class"):
        driver.execute_script("arguments[0].click();", star)
        time.sleep(0.5)
    
    driver.execute_script("arguments[0].click();", star)
    wait.until(lambda d: "active" in star.get_attribute("class"))
    
    # Reload
    driver.refresh()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    # Find the same star
    star_after = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f".star-icon[data-problem-id='{problem_id}']")))
    assert "active" in star_after.get_attribute("class")

def test_favorite_filter(driver, base_url, wait):
    """Test filtering by favorites."""
    driver.get(base_url)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    time.sleep(1)
    
    # Mark first item as favorite
    stars = driver.find_elements(By.CLASS_NAME, "star-icon")
    if not stars:
        pytest.skip("No problems found")
        
    first_star = stars[0]
    if "active" not in first_star.get_attribute("class"):
        driver.execute_script("arguments[0].click();", first_star)
    
    # Enable filter
    filter_chk = driver.find_element(By.ID, "show-favorites-only")
    driver.execute_script("arguments[0].click();", filter_chk)
    
    # Verify only favorites are shown
    # Wait for list update
    time.sleep(0.5)
    visible_stars = driver.find_elements(By.CSS_SELECTOR, ".problem-card .star-icon")
    for s in visible_stars:
        assert "active" in s.get_attribute("class")
