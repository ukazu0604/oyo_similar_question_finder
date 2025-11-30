import json
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000/"



def test_content_is_rendered(driver, page_load_waiter):
    """JSONが読み込まれ、カテゴリリストが描画されるかテストする。"""
    driver.get(BASE_URL)
    page_load_waiter()
    
    categories = driver.find_elements(By.CLASS_NAME, "middle-category-item")
    assert len(categories) > 0, "カテゴリコンテナが1つ以上表示されるべきです。"



def test_stacked_progress_bar(driver, page_load_waiter):
    """
    積み上げ式プログレスバーが状態に応じて正しく表示されるかテスト
    """
    driver.get(BASE_URL)
    page_load_waiter()
    
    # アプリケーションが完全に初期化されるまで待機
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return window.state && window.state.data && window.state.data.categories !== undefined;")
    )
    
    # 0. テストの前提となる情報を取得
    # 総問題数を取得するために、JavaScriptを実行する
    total_problems = driver.execute_script("""
        try {
            return Object.values(window.state.data.categories).reduce((sum, problems) => sum + problems.length, 0);
        } catch (e) {
            return 0;
        }
    """)
    if total_problems < 3:
        pytest.skip("テスト実行には少なくとも3問以上必要です")
    # 問題IDを3つ取得
    problem_ids = driver.execute_script("""
        const ids = [];
        for (const cat in window.state.data.categories) {
            for (const item of window.state.data.categories[cat]) {
                ids.push(`${item.main_problem.出典}-${item.main_problem.問題番号}`);
                if (ids.length >= 3) return ids;
            }
        }
        return ids;
    """)
    completed_id = problem_ids[0]
    archived_id = problem_ids[1]
    completed_and_archived_id = problem_ids[2]

    # 1. 状態をlocalStorageにセット
    #   - 1問を完了 (4/4チェック)
    #   - 1問をアーカイブ
    #   - 1問を完了かつアーカイブ (アーカイブが優先されることを確認)
    check_data = {
        completed_id: [
            {"checked": True, "timestamp": 1}, {"checked": True, "timestamp": 1},
            {"checked": True, "timestamp": 1}, {"checked": True, "timestamp": 1}
        ],
        completed_and_archived_id: [
            {"checked": True, "timestamp": 1}, {"checked": True, "timestamp": 1},
            {"checked": True, "timestamp": 1}, {"checked": True, "timestamp": 1}
        ]
    }
    archived_data = [archived_id, completed_and_archived_id]
    
    driver.execute_script(f"localStorage.setItem('oyo_problemChecks', JSON.stringify({json.dumps(check_data)}));")
    driver.execute_script(f"localStorage.setItem('oyo_archivedProblemIds', JSON.stringify({json.dumps(archived_data)}));")
    
    # 2. リロードして状態を反映
    driver.refresh()
    page_load_waiter()
    time.sleep(1) # 描画完了を待つ

    # 3. バーの幅とテキストを検証
    # 完了: 1問, アーカイブ: 2問
    expected_completed_pct = (1 / total_problems) * 100
    expected_archived_pct = (2 / total_problems) * 100

    completed_bar = driver.find_element(By.CSS_SELECTOR, ".progress-bar-completed")
    archived_bar = driver.find_element(By.CSS_SELECTOR, ".progress-bar-archived")
    
    # widthの小数点以下を考慮して比較
    completed_width = float(completed_bar.get_attribute("style").split(":")[1].replace("%;", "").strip())
    archived_width = float(archived_bar.get_attribute("style").split(":")[1].replace("%;", "").strip())

    assert abs(completed_width - expected_completed_pct) < 0.01, f"完了バーの幅が期待値と異なります。期待値: {expected_completed_pct}%, 実際: {completed_width}%"
    assert abs(archived_width - expected_archived_pct) < 0.01, f"アーカイブバーの幅が期待値と異なります。期待値: {expected_archived_pct}%, 実際: {archived_width}%"

    # テキストの検証
    legend_text = driver.find_element(By.CLASS_NAME, "progress-legend").text
    assert f"完了: 1.0問 ({expected_completed_pct:.1f}%)" in legend_text
    assert f"アーカイブ: 2問 ({expected_archived_pct:.1f}%)" in legend_text
