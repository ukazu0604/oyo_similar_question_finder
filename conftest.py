"""
==============================================
ヘッドレスモード設定（Seleniumテスト）
==============================================
True:  ヘッドレスモード（ブラウザを表示しない）
False: 通常モード（ブラウザを表示する）
==============================================
"""
RUN_HEADLESS = True  # ← ここをTrue/Falseで切り替え

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os # 追加: osモジュールをインポート
import sys # 追加: sysモジュールをインポート

# --- テスト設定ファイルの読み込み ---
try:
    from .test_settings.local import TEST_GAS_URL # .test_settings.local から TEST_GAS_URL をインポート
except ImportError:
    # .test_settings.local が見つからない、または TEST_GAS_URL が定義されていない場合
    # run_all_tests.py で既にチェックしているはずだが、念のためここでもエラーにする
    print(f"エラー: '.test_settings.local' ファイルが見つからないか、TEST_GAS_URLが定義されていません。", file=sys.stderr)
    print(f"'py create_test_config.py' を実行してファイルを作成し、テスト用のGAS URLを設定してください。", file=sys.stderr)
    sys.exit(1) # テスト実行を中断

# TEST_GAS_URL が空文字列の場合もエラー
if not TEST_GAS_URL or TEST_GAS_URL == "https://script.google.com/macros/s/YOUR_TEST_GAS_URL_HERE/exec":
    print(f"エラー: '.test_settings.local' の TEST_GAS_URL が設定されていません。", file=sys.stderr)
    print(f"ファイルを開き、適切なテスト用のGAS URLを設定してください。", file=sys.stderr)
    sys.exit(1) # テスト実行を中断


@pytest.fixture(scope="module")
def driver():
    """
    Selenium WebDriverのインスタンスを提供するpytest fixture。
    テストモジュール実行中に一度だけブラウザを起動し、終了時に閉じる。
    """
    chrome_options = Options()
    
    # ヘッドレスモード設定
    if RUN_HEADLESS:
        print("\n--- Running in headless mode setting (Selenium test) ---")
        chrome_options.add_argument("--headless=new")  # 新しいヘッドレスモード
        chrome_options.add_argument("--disable-gpu")  # GPU無効化（Windows推奨）
    
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=0") # Seleniumの冗長なログを抑制
    # コンソールログを取得するための設定
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    service = ChromeService(ChromeDriverManager().install())
    web_driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # --- ここから追加するロジック ---
    # ブラウザ起動後、localStorageにGAS URLを設定
    print(f"--- Setting GAS URL in localStorage for tests: {TEST_GAS_URL} ---")
    web_driver.execute_script(f"localStorage.setItem('oyo_gasUrl', '{TEST_GAS_URL}');")
    # --- ここまで追加するロジック ---

    yield web_driver # テスト関数にWebDriverインスタンスを渡す
    
    # --- クリーンアップロジック ---
    print("--- Cleaning up localStorage after tests ---")
    web_driver.execute_script("localStorage.removeItem('oyo_gasUrl');")
    # --- クリーンアップロジックここまで ---

    web_driver.quit() # テストモジュール終了後にブラウザを閉じる


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException # Added this import


@pytest.fixture
def page_load_waiter(driver):
    """
    app.jsによってコンテンツが描画されるのを待ち、深刻なコンソールエラーがないかチェックするヘルパー関数。
    """
    def _wait_for_page_load():
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#category-list > div"))
            )
            WebDriverWait(driver, 60).until(
                lambda driver: driver.execute_script("return window.appInitialized === true")
            )
        except TimeoutException:
            print("\n--- TimeoutException during page load. Diagnostic Info: ---")
            print(f"Current URL: {driver.current_url}")
            print("\n--- Page Source (at timeout): ---")
            print(driver.page_source)
            print("-----------------------------------")
            try:
                app_initialized_status = driver.execute_script("return window.appInitialized;")
                print(f"window.appInitialized: {app_initialized_status}")
            except Exception as e:
                print(f"Could not get window.appInitialized: {e}")
            try:
                browser_logs = driver.get_log('browser')
                if browser_logs:
                    print("\n--- Browser Logs (at timeout): ---")
                    for log in browser_logs:
                        print(log)
                    print("------------------------------------")
                else:
                    print("\n--- No Browser Logs Captured. ---")
            except Exception as e:
                print(f"Could not get browser logs: {e}")
            
            print("-------------------------------------------------------")
            pytest.fail("ページロードがタイムアウトしました。診断情報を確認してください。")

        logs = driver.get_log('browser')
        severe_errors = [log for log in logs if log['level'] == 'SEVERE']
        # ページロード後にコンソールエラーがないかチェック
        logs = driver.get_log('browser')
        severe_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if severe_errors:
            messages = [err['message'] for err in severe_errors]
            pytest.fail(f"ページロード中に深刻なコンソールエラーが検出されました:\n{messages}")
    return _wait_for_page_load
