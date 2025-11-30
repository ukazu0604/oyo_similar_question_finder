import json
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8000/"



def test_content_is_rendered(driver, page_load_waiter, login_test_user):
    """JSONが読み込まれ、カテゴリリストが描画されるかテストする。"""
    driver.get(BASE_URL) # ページをロード
    page_load_waiter()   # アプリケーションの初期化完了を待つ
    login_test_user()    # その後にログイン
    
    categories = driver.find_elements(By.CLASS_NAME, "middle-category-item")
    assert len(categories) > 0, "カテゴリコンテナが1つ以上表示されるべきです。"



def test_stacked_progress_bar(driver, page_load_waiter, login_test_user):
    """
    積み上げ式プログレスバーが状態に応じて正しく表示されるかテスト
    """
    driver.get(BASE_URL) # ページをロード
    page_load_waiter()   # アプリケーションの初期化完了を待つ
    login_test_user()    # その後にログイン
    
    # 0. テストの前提となる情報を取得
    # 総問題数を取得するために、JavaScriptを実行する
    total_problems = driver.execute_script("""
        try {
            let sum = 0;
            for (const cat in window.state.data.categories) {
                sum += window.state.data.categories[cat].length;
            }
            return sum;
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
    
    # デバッグ出力の追加
    print(f"\nDebug: total_problems = {total_problems}")
    print(f"Debug: expected_completed_pct (1 completed) = {(1 / total_problems) * 100}%")
    print(f"Debug: expected_archived_pct (2 archived) = {(2 / total_problems) * 100}%")

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
    
    # storage.jsのgetCurrentUserId()のロジックに合わせてキーを生成
    # JavaScriptを介してstorage.getCurrentUserId()を取得
    user_id = driver.execute_script("return storage.getCurrentUserId();")
    
    # キー名を生成 (storage.jsのロジックと一致させる)
    problem_checks_key = f"oyo_problemChecks_{user_id}" if user_id else 'oyo_problemChecks_default';
    archived_ids_key = f"oyo_archivedProblemIds_{user_id}" if user_id else 'oyo_archivedProblemIds_default';
    
    driver.execute_script(f"localStorage.setItem('{problem_checks_key}', JSON.stringify({json.dumps(check_data)}));")
    driver.execute_script(f"localStorage.setItem('{archived_ids_key}', JSON.stringify({json.dumps(archived_data)}));")
    
    # 2. リロードして状態を反映
    driver.refresh()
    page_load_waiter()
    # time.sleep(1) # 描画完了を待つ (これはpage_load_waiterでカバーされているはずなので不要)

    # window.state.calculatedCompletedCount と calculatedArchivedCount が更新されるのを待つ
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script(
            "return typeof window.state.calculatedCompletedCount === 'number' && "
            "typeof window.state.calculatedArchivedCount === 'number';"
        ),
        message="window.state.calculatedCompletedCount または calculatedArchivedCount が有効な数値に更新されません"
    )

    # 3. バーの幅とテキストを検証
    # アプリケーションが計算した完了数とアーカイブ数を直接取得
    completed_count_from_app = driver.execute_script(
        "return window.state.calculatedCompletedCount || 0;"
    )
    archived_count_from_app = driver.execute_script(
        "return window.state.calculatedArchivedCount || 0;"
    )

    print(f"Debug: completed_count_from_app = {completed_count_from_app}")
    print(f"Debug: archived_count_from_app = {archived_count_from_app}")

    expected_completed_pct = (completed_count_from_app / total_problems) * 100
    expected_archived_pct = (archived_count_from_app / total_problems) * 100


    completed_bar = driver.find_element(By.CSS_SELECTOR, ".progress-bar-completed")
    archived_bar = driver.find_element(By.CSS_SELECTOR, ".progress-bar-archived")
    
    # widthの小数点以下を考慮して比較
    completed_width = float(completed_bar.get_attribute("style").split(":")[1].replace("%;", "").strip())
    archived_width = float(archived_bar.get_attribute("style").split(":")[1].replace("%;", "").strip())

    assert abs(completed_width - expected_completed_pct) < 0.01, f"完了バーの幅が期待値と異なります。期待値: {expected_completed_pct}%, 実際: {completed_width}%"
    assert abs(archived_width - expected_archived_pct) < 0.01, f"アーカイブバーの幅が期待値と異なります。期待値: {expected_archived_pct}%, 実際: {archived_width}%"

    # テキストの検証
    legend_text = driver.find_element(By.CLASS_NAME, "progress-legend").text
    assert f"完了: {completed_count_from_app:.1f}問 ({expected_completed_pct:.1f}%)" in legend_text
    assert f"アーカイブ: {archived_count_from_app}問 ({expected_archived_pct:.1f}%)" in legend_text