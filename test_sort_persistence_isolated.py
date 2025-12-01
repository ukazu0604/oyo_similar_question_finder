import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from conftest import page_load_waiter, login_test_user, BASE_URL

@pytest.fixture
def simple_reset(driver):
    """このテスト専用のシンプルなリセットフィクスチャ"""
    print("\n--- [ISOLATED TEST] Clearing localStorage ---")
    driver.get(BASE_URL)
    driver.execute_script("localStorage.clear();")
    driver.refresh()

def test_sort_order_persistence_isolated(driver, page_load_waiter, login_test_user, simple_reset):
    """
    ソート順を変更し、リロード後もその設定が維持されることを確認する隔離テスト
    """
    page_load_waiter()
    login_test_user()
    
    # カテゴリを開く
    major_title = driver.find_element(By.CLASS_NAME, "major-title")
    list_el = major_title.find_element(By.XPATH, "following-sibling::div[contains(@class, 'middle-category-list')]")
    if not list_el.is_displayed():
        major_title.click()
        WebDriverWait(driver, 2).until(EC.visibility_of(list_el))

    # 詳細画面へ移動
    driver.find_element(By.CSS_SELECTOR, ".middle-category-link").click()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "detail-view")))
    
    # hasReviewItems が false であることを確認（デバッグ）
    has_review_items = driver.execute_script("""
        const middleCat = document.getElementById('detail-title').textContent;
        const problemsForCheck = window.state.data.categories[middleCat];
        return problemsForCheck.some(item => {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
            return window.shouldHighlightProblem(problemId, window.state.problemChecks);
        });
    """)
    print(f"--- [ISOLATED TEST] hasReviewItems = {has_review_items} ---")
    assert not has_review_items, "このテストは hasReviewItems が false の状態で実行されるべきです"


    # ソート順を変更 (例: 参照順)
    select = Select(driver.find_element(By.ID, "sort-order"))
    select.select_by_value("ref-desc")
    time.sleep(0.5) 
    
    # localStorageに保存されたか確認（デバッグ）
    saved_sort_order = driver.execute_script("return localStorage.getItem('oyo_currentSortOrder_a');") # ユーザーIDは 'a' と仮定
    print(f"--- [ISOLATED TEST] Saved sort order in localStorage = {saved_sort_order} ---")
    assert saved_sort_order == "ref-desc"

    # リロード
    driver.refresh()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "detail-view")))

    # リロード後にlocalStorageに値が残っているか確認（デバッグ）
    reloaded_sort_order = driver.execute_script("return localStorage.getItem('oyo_currentSortOrder_a');")
    print(f"--- [ISOLATED TEST] Reloaded sort order in localStorage = {reloaded_sort_order} ---")
    assert reloaded_sort_order == "ref-desc"
    
    # 選択状態が維持されているか確認
    select_after = Select(driver.find_element(By.ID, "sort-order"))
    assert select_after.first_selected_option.get_attribute("value") == "ref-desc"
