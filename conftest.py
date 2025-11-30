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
    
    yield web_driver # テスト関数にWebDriverインスタンスを渡す
    
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