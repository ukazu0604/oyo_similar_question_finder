import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from .conftest import wait_for_overlays_to_disappear

def test_navigation(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test navigation from index to detail and back."""
    # driver.get(base_url) handled by fixture
    
    wait_for_overlays_to_disappear(driver)
    
    # Click first category
    category_link = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link")))
    category_name = category_link.get_attribute("data-cat")
    category_link.click()
    
    # Verify detail view
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    detail_title = driver.find_element(By.ID, "detail-title")
    assert detail_title.text == category_name
    assert driver.find_element(By.ID, "index-view").is_displayed() == False
    
    # Click back button
    back_btn = wait.until(EC.element_to_be_clickable((By.ID, "back-button")))
    back_btn.click()
    
    # Verify index view
    wait.until(EC.visibility_of_element_located((By.ID, "index-view")))
    assert driver.find_element(By.ID, "detail-view").is_displayed() == False

def test_sort_persistence(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test that sort order is persisted after reload."""
    
    wait_for_overlays_to_disappear(driver)
    # Go to detail view
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    # Change sort order
    sort_select = Select(driver.find_element(By.ID, "sort-order"))
    sort_select.select_by_value("like-desc")
    
    # Reload
    driver.refresh()
    
    # Verify we are still in detail view (hash routing) or navigate back
    # The app uses hash routing?
    # app.js: showDetail(decodeURIComponent(initialHash), true);
    # If hash is present, it stays.
    # Let's check if hash is set.
    # js/ui-index.js: navigateToDetail sets location.hash.
    
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    # Verify sort order
    sort_select = Select(wait.until(EC.presence_of_element_located((By.ID, "sort-order"))))
    assert sort_select.first_selected_option.get_attribute("value") == "like-desc"

def test_checkboxes(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test checkbox interaction."""
    # driver.get(base_url) handled by fixture
    
    wait_for_overlays_to_disappear(driver)
    # Go to detail view
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    # Find a checkbox
    checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".check-box[data-check-index='0']")))
    
    # Ensure it's clickable (might need to scroll or wait for overlay to go)
    # Also wait for isReadOnlyMode to be false (notification might appear)
    wait.until(lambda d: d.execute_script("return not window.isReadOnlyMode"))
    
    # Click it
    driver.execute_script("arguments[0].click();", checkbox) # Use JS to avoid interception
    
    # Verify checked class
    wait.until(lambda d: "checked" in checkbox.get_attribute("class"))
    
    # Click again to uncheck
    driver.execute_script("arguments[0].click();", checkbox)
    wait.until(lambda d: "checked" not in checkbox.get_attribute("class"))

def test_reaction_buttons(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test reaction buttons."""

    wait_for_overlays_to_disappear(driver)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    wait.until(lambda d: d.execute_script("return not window.isReadOnlyMode")) 
    
    # Find a like button
    btn = driver.find_element(By.CSS_SELECTOR, ".reaction-button[data-reaction-type='like']")
    count_span = btn.find_element(By.XPATH, "following-sibling::span[contains(@class, 'reaction-count')]")
    initial_count = int(count_span.text)
    
    driver.execute_script("arguments[0].click();", btn)
    
    wait.until(lambda d: int(count_span.text) == initial_count + 1)

def test_archive(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test archive functionality."""

    wait_for_overlays_to_disappear(driver)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    wait.until(lambda d: d.execute_script("return not window.isReadOnlyMode"))
    
    archive_btn = driver.find_element(By.CLASS_NAME, "archive-button")
    initial_text = archive_btn.text
    
    driver.execute_script("arguments[0].click();", archive_btn)
    
    wait.until(lambda d: archive_btn.text != initial_text)
    assert "元に戻す" in archive_btn.text if "アーカイブ" in initial_text else "アーカイブ" in archive_btn.text

def test_favorites(driver, base_url, wait, setup_gas_url, auto_login_mock):
    """Test favorite toggle."""

    wait_for_overlays_to_disappear(driver)
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "middle-category-link"))).click()
    wait.until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    wait.until(lambda d: d.execute_script("return not window.isReadOnlyMode"))
    
    star = driver.find_element(By.CLASS_NAME, "star-icon")
    driver.execute_script("arguments[0].click();", star)
    
    wait.until(lambda d: "active" in star.get_attribute("class"))
    
    driver.execute_script("arguments[0].click();", star)
    wait.until(lambda d: "active" not in star.get_attribute("class"))
