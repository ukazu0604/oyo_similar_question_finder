# -*- coding: utf-8 -*-
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
import os
import sys

# プロジェクトのルートディレクトリをsys.pathに追加
# conftest.pyがルートにあると仮定
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 追加: SeleniumのWebDriverWaitとExpectedConditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


# --- テスト設定ファイルの読み込み ---
try:
    from test_settings import TEST_GAS_URL, TEST_USER_ID, TEST_PASSWORD
except ImportError:
    print(f"エラー: 'test_settings.py' ファイルが見つからないか、必要な変数が定義されていません。", file=sys.stderr)
    print(f"'py create_test_config.py' を実行してファイルを作成し、テスト用のGAS URL、ユーザーID、パスワードを設定してください。", file=sys.stderr)
    sys.exit(1)

# TEST_GAS_URL のバリデーション
if not TEST_GAS_URL or TEST_GAS_URL == "https://script.google.com/macros/s/YOUR_TEST_GAS_URL_HERE/exec":
    print(f"エラー: '.test_settings.local' の TEST_GAS_URL が設定されていません。", file=sys.stderr)
    print(f"ファイルを開き、適切なテスト用のGAS URLを設定してください。", file=sys.stderr)
    sys.exit(1)

# TEST_USER_ID と TEST_PASSWORD のバリデーション
if not TEST_USER_ID or TEST_USER_ID == "testuser":
    print(f"エラー: '.test_settings.local' の TEST_USER_ID が設定されていません。", file=sys.stderr)
    print(f"ファイルを開き、適切なテスト用のユーザーIDを設定してください。", file=sys.stderr)
    sys.exit(1)

if not TEST_PASSWORD or TEST_PASSWORD == "testpassword":
    print(f"エラー: '.test_settings.local' の TEST_PASSWORD が設定されていません。", file=sys.stderr)
    print(f"ファイルを開き、適切なテスト用のパスワードを設定してください。", file=sys.stderr)
    sys.exit(1)


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
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
    
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=0")
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    service = ChromeService(ChromeDriverManager().install())
    web_driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print(f"--- Setting GAS URL in localStorage for tests: {TEST_GAS_URL} ---")
    web_driver.execute_script(f"localStorage.setItem('oyo_gasUrl', '{TEST_GAS_URL}');")

    yield web_driver
    
    print("--- Cleaning up localStorage after tests ---")
    web_driver.execute_script("localStorage.removeItem('oyo_gasUrl');")
    web_driver.quit()


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
        
        if severe_errors:
            messages = [err['message'] for err in severe_errors]
            pytest.fail(f"ページロード中に深刻なコンソールエラーが検出されました:\n{messages}")
    return _wait_for_page_load

@pytest.fixture
def login_test_user(driver, page_load_waiter):
    """
    テストユーザーとしてアプリケーションにログインするフィクスチャ。
    """
    def _login():
        print(f"\n--- Logging in as test user: {TEST_USER_ID} ---")
        
        # ログインモーダルを開く
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "auth-button"))).click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        # ユーザーIDとパスワードを入力
        driver.find_element(By.ID, "login-user-id").send_keys(TEST_USER_ID)
        driver.find_element(By.ID, "login-password").send_keys(TEST_PASSWORD)
        
        # ログインボタンをクリック
        driver.find_element(By.ID, "login-button").click()
        
        # ログイン成功を待機 (例: ログインモーダルが閉じる、またはユーザー名が表示される)
        WebDriverWait(driver, 20).until(EC.invisibility_of_element_located((By.ID, "login-modal")))
        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.ID, "current-user-display"), TEST_USER_ID))
        
        print(f"--- Successfully logged in as {TEST_USER_ID} ---")
    
    return _login