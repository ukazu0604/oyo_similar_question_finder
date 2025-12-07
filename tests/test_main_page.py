import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def test_content_display(driver, base_url, wait):
    """Verify that the main page loads and displays categories."""
    driver.get(base_url)
    
    # Check title
    assert "応用情報技術者試験" in driver.title
    
    # Check category list is populated
    category_list = wait.until(EC.presence_of_element_located((By.ID, "category-list")))
    
    # Wait for at least one category section to appear
    wait.until(lambda d: len(category_list.find_elements(By.CLASS_NAME, "category-section")) > 0)
    
    categories = category_list.find_elements(By.CLASS_NAME, "category-section")
    assert len(categories) > 0
    
    # Check model info is loaded
    model_info = driver.find_element(By.ID, "model-info")
    wait.until(lambda d: model_info.text != "読み込み中...")
    assert model_info.text != ""

def test_progress_bar(driver, base_url, wait):
    """Verify that the progress bar container is displayed."""
    driver.get(base_url)
    
    progress_container = wait.until(EC.presence_of_element_located((By.ID, "total-progress-container")))
    assert progress_container.is_displayed()
    
    # Ideally check for content inside, but it depends on data state.
    # We assume if container is there, it's rendered.
