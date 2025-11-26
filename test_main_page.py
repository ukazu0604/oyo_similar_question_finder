import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000/"

def wait_for_page_load(driver):
    """
    app.jsによってコンテンツが描画されるのを待つヘルパー関数。
    """
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#category-list > div"))
    )

def test_content_is_rendered(driver):
    """JSONが読み込まれ、カテゴリリストが描画されるかテストする。"""
    driver.get(BASE_URL)
    wait_for_page_load(driver)
    
    categories = driver.find_elements(By.CLASS_NAME, "middle-category-item")
    assert len(categories) > 0, "カテゴリコンテナが1つ以上表示されるべきです。"

def test_no_severe_console_errors(driver):
    """ブラウザコンソールに深刻な(SEVERE)エラーがないかテストする。"""
    driver.get(BASE_URL)
    wait_for_page_load(driver)
    time.sleep(1) # 非同期処理が完了するのを少し待つ

    logs = driver.get_log('browser')
    severe_errors = [log for log in logs if log['level'] == 'SEVERE']
    
    if severe_errors:
        messages = [err['message'] for err in severe_errors]
        pytest.fail(f"深刻なコンソールエラーが検出されました:\n{messages}")

    assert not severe_errors
