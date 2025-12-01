import pytest
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "http://localhost:8000/"

def mock_gas_api(driver, custom_responses=None):
    """
    Injects a mock fetch function to intercept GAS API calls.
    This allows testing without a real GAS backend.
    
    Args:
        driver: Selenium WebDriver instance
        custom_responses: Optional dict to override default mock responses
    """
    default_responses = {
        'login': {'success': True, 'accessToken': 'mock_access_token', 'refreshToken': 'mock_refresh_token', 'userId': 'testuser'},
        'register': {'success': True, 'message': 'User registered successfully'},
        'save': {'success': True, 'version': 1},
        'load': {'success': True, 'data': {'test_key': 'test_value'}, 'version': 1},
        'validate': {'valid': True, 'userId': 'testuser'},
        'refresh': {'success': True, 'accessToken': 'new_mock_access_token', 'userId': 'testuser'}
    }
    
    if custom_responses:
        default_responses.update(custom_responses)
    
    mock_script = f"""
    window.originalFetch = window.fetch;
    window.mockGasResponse = {json.dumps(default_responses)};

    window.fetch = async (url, options) => {{
        if (url.includes('script.google.com')) {{
            console.log('Mocking GAS request:', url, options);
            const body = JSON.parse(options.body);
            const action = body.action;
            
            // Simulate network delay
            await new Promise(r => setTimeout(r, 100));

            if (window.mockGasResponse[action]) {{
                const response = window.mockGasResponse[action];
                // Simulate error if configured
                if (response.error) {{
                    return {{
                        ok: true,
                        json: async () => response
                    }};
                }}
                return {{
                    ok: true,
                    json: async () => response
                }};
            }}
            return {{ ok: true, json: async () => ({{ error: 'Unknown action' }}) }};
        }}
        return window.originalFetch(url, options);
    }};
    """
    driver.execute_script(mock_script)


class TestLoginModalUI:
    """ログインモーダルのUI表示テスト"""
    
    def test_login_modal_opens(self, driver, page_load_waiter):
        """ログインボタンをクリックしてモーダルが表示されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        # ログインボタンをクリック
        auth_button = driver.find_element(By.ID, "auth-button")
        auth_button.click()
        
        # モーダルが表示されることを確認
        login_modal = WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.ID, "login-modal"))
        )
        assert login_modal.is_displayed()
    
    def test_login_modal_elements_exist(self, driver, page_load_waiter):
        """モーダル内に必要な要素が存在することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        # 必要な要素の存在確認
        assert driver.find_element(By.ID, "login-user-id").is_displayed()
        assert driver.find_element(By.ID, "login-password").is_displayed()
        assert driver.find_element(By.ID, "login-button").is_displayed()
        assert driver.find_element(By.ID, "register-button").is_displayed()
        assert driver.find_element(By.ID, "close-login-modal").is_displayed()
    
    def test_login_modal_closes_with_button(self, driver, page_load_waiter):
        """モーダルの閉じるボタンで正しく閉じることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        # 閉じるボタンをクリック
        driver.find_element(By.ID, "close-login-modal").click()
        time.sleep(0.3)
        
        # モーダルが非表示になることを確認
        login_modal = driver.find_element(By.ID, "login-modal")
        assert login_modal.value_of_css_property("display") == "none"
    
    def test_login_modal_closes_with_outside_click(self, driver, page_load_waiter):
        """モーダル外をクリックして閉じることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        # モーダルの背景をクリック
        login_modal = driver.find_element(By.ID, "login-modal")
        driver.execute_script("arguments[0].click();", login_modal)
        time.sleep(0.3)
        
        # モーダルが非表示になることを確認
        assert login_modal.value_of_css_property("display") == "none"


class TestLoginSuccess:
    """ログイン成功パターンのテスト"""
    
    def test_successful_login(self, driver, page_load_waiter):
        """正しい認証情報でログインが成功することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        # ログインモーダルを開く
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        # 認証情報を入力
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        
        # ログインボタンをクリック
        driver.find_element(By.ID, "login-button").click()
        
        # ログイン成功メッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "ログイン成功" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_tokens_saved_to_localstorage(self, driver, page_load_waiter):
        """ログイン後にlocalStorageにトークンが保存されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "login-button").click()
        
        # ログイン成功を待つ
        WebDriverWait(driver, 5).until(
            lambda d: "ログイン成功" in d.find_element(By.ID, "auth-status").text
        )
        
        # localStorageにトークンが保存されていることを確認
        tokens = driver.execute_script(
            "return {access: localStorage.getItem('oyo_accessToken'), refresh: localStorage.getItem('oyo_refreshToken')}"
        )
        assert tokens['access'] == 'mock_access_token'
        assert tokens['refresh'] == 'mock_refresh_token'
    
    def test_user_display_updated_after_login(self, driver, page_load_waiter):
        """ログイン後にユーザー表示が更新されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "login-button").click()
        
        # ユーザー表示が更新されることを確認
        WebDriverWait(driver, 5).until(
            lambda d: "testuser" in d.find_element(By.ID, "current-user-display").text
        )
    
    def test_page_reloads_after_login(self, driver, page_load_waiter):
        """ログイン後にページがリロードされることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        # ページにマーカーを設定
        driver.execute_script("window.testMarker = 'before_login';")
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "login-button").click()
        
        # ログイン成功を待つ
        WebDriverWait(driver, 5).until(
            lambda d: "ログイン成功" in d.find_element(By.ID, "auth-status").text
        )
        
        # リロードを待つ
        time.sleep(1.5)
        page_load_waiter()
        
        # マーカーが消えていることを確認(ページがリロードされた証拠)
        marker = driver.execute_script("return window.testMarker;")
        assert marker is None


class TestLoginFailure:
    """ログイン失敗パターンのテスト"""
    
    def test_login_with_invalid_user(self, driver, page_load_waiter):
        """存在しないユーザーIDでログインが失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # ユーザーが存在しないエラーを返すモックを設定
        mock_gas_api(driver, {'login': {'error': 'User not found'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("nonexistent")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "login-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "エラー" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_login_with_wrong_password(self, driver, page_load_waiter):
        """間違ったパスワードでログインが失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        mock_gas_api(driver, {'login': {'error': 'Invalid password'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("wrongpassword")
        driver.find_element(By.ID, "login-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "エラー" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_login_with_empty_userid(self, driver, page_load_waiter):
        """空のユーザーIDでログインが失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        mock_gas_api(driver, {'login': {'error': 'Missing userId or password'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "login-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "エラー" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_login_with_empty_password(self, driver, page_load_waiter):
        """空のパスワードでログインが失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        mock_gas_api(driver, {'login': {'error': 'Missing userId or password'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("")
        driver.find_element(By.ID, "login-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "エラー" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_error_message_displayed(self, driver, page_load_waiter):
        """エラーメッセージが適切に表示されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        mock_gas_api(driver, {'login': {'error': 'Test error message'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "login-button").click()
        
        # エラーメッセージの内容を確認
        auth_status = WebDriverWait(driver, 5).until(
            lambda d: d.find_element(By.ID, "auth-status")
        )
        assert "Test error message" in auth_status.text


class TestRegistration:
    """新規登録パターンのテスト"""
    
    def test_successful_registration(self, driver, page_load_waiter):
        """新規ユーザーの登録が成功することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("newuser")
        driver.find_element(By.ID, "login-password").send_keys("newpassword123")
        driver.find_element(By.ID, "register-button").click()
        
        # 登録成功メッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "登録成功" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_registration_prompts_login(self, driver, page_load_waiter):
        """登録成功後にログインを促すメッセージが表示されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        mock_gas_api(driver)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("newuser")
        driver.find_element(By.ID, "login-password").send_keys("newpassword123")
        driver.find_element(By.ID, "register-button").click()
        
        # ログインを促すメッセージを確認
        auth_status = WebDriverWait(driver, 5).until(
            lambda d: d.find_element(By.ID, "auth-status")
        )
        assert "ログインしてください" in auth_status.text
    
    def test_registration_with_existing_user(self, driver, page_load_waiter):
        """既存ユーザーIDで登録が失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        mock_gas_api(driver, {'register': {'error': 'User already exists'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("existinguser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "register-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "エラー" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_registration_with_empty_userid(self, driver, page_load_waiter):
        """空のユーザーIDで登録が失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        mock_gas_api(driver, {'register': {'error': 'Missing userId or password'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "register-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "エラー" in d.find_element(By.ID, "auth-status").text
        )
    
    def test_registration_with_empty_password(self, driver, page_load_waiter):
        """空のパスワードで登録が失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        mock_gas_api(driver, {'register': {'error': 'Missing userId or password'}})
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("newuser")
        driver.find_element(By.ID, "login-password").send_keys("")
        driver.find_element(By.ID, "register-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "エラー" in d.find_element(By.ID, "auth-status").text
        )


class TestTokenValidation:
    """トークン検証パターンのテスト"""
    
    def test_valid_access_token_auto_login(self, driver, page_load_waiter):
        """有効なaccessTokenで自動ログインが成功することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # 有効なトークンを設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'valid_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        
        driver.refresh()
        page_load_waiter()
        mock_gas_api(driver)
        
        # 少し待ってから確認
        time.sleep(1)
        
        # ユーザー表示が更新されていることを確認
        user_display = driver.find_element(By.ID, "current-user-display").text
        assert "testuser" in user_display
    
    def test_invalid_access_token_validation_fails(self, driver, page_load_waiter):
        """無効なaccessTokenで検証が失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # 無効なトークンを設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'invalid_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        
        # 検証失敗のモックを設定
        mock_gas_api(driver, {'validate': {'valid': False}})
        
        driver.refresh()
        page_load_waiter()
        
        # 少し待ってから確認
        time.sleep(1)
        
        # ログインモーダルが表示されることを確認
        login_modal = driver.find_element(By.ID, "login-modal")
        assert login_modal.value_of_css_property("display") == "block"
    
    def test_expired_access_token_validation_fails(self, driver, page_load_waiter):
        """期限切れのaccessTokenで検証が失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # 期限切れトークンを設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'expired_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        
        # 検証失敗のモックを設定
        mock_gas_api(driver, {'validate': {'valid': False, 'error': 'Token expired'}})
        
        driver.refresh()
        page_load_waiter()
        
        # 少し待ってから確認
        time.sleep(1)
        
        # ログインモーダルが表示されることを確認
        login_modal = driver.find_element(By.ID, "login-modal")
        assert login_modal.value_of_css_property("display") == "block"


class TestTokenRefresh:
    """トークンリフレッシュパターンのテスト"""
    
    def test_valid_refresh_token_updates_access_token(self, driver, page_load_waiter):
        """有効なrefreshTokenでaccessTokenが更新されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # 無効なアクセストークンと有効なリフレッシュトークンを設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'expired_access_token');")
        driver.execute_script("localStorage.setItem('oyo_refreshToken', 'valid_refresh_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        
        # 検証失敗、リフレッシュ成功のモックを設定
        mock_gas_api(driver, {
            'validate': {'valid': False},
            'refresh': {'success': True, 'accessToken': 'new_access_token', 'userId': 'testuser'}
        })
        
        driver.refresh()
        page_load_waiter()
        
        # 少し待ってから確認
        time.sleep(1)
        
        # 新しいアクセストークンが保存されていることを確認
        new_token = driver.execute_script("return localStorage.getItem('oyo_accessToken');")
        assert new_token == 'new_access_token'
    
    def test_invalid_refresh_token_fails(self, driver, page_load_waiter):
        """無効なrefreshTokenでリフレッシュが失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'expired_access_token');")
        driver.execute_script("localStorage.setItem('oyo_refreshToken', 'invalid_refresh_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        
        # 検証失敗、リフレッシュ失敗のモックを設定
        mock_gas_api(driver, {
            'validate': {'valid': False},
            'refresh': {'error': 'Invalid or expired refresh token'}
        })
        
        driver.refresh()
        page_load_waiter()
        
        # 少し待ってから確認
        time.sleep(1)
        
        # ログインモーダルが表示されることを確認
        login_modal = driver.find_element(By.ID, "login-modal")
        assert login_modal.value_of_css_property("display") == "block"
    
    def test_expired_refresh_token_fails(self, driver, page_load_waiter):
        """期限切れのrefreshTokenでリフレッシュが失敗することを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'expired_access_token');")
        driver.execute_script("localStorage.setItem('oyo_refreshToken', 'expired_refresh_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        
        # 検証失敗、リフレッシュ失敗のモックを設定
        mock_gas_api(driver, {
            'validate': {'valid': False},
            'refresh': {'error': 'Invalid or expired refresh token'}
        })
        
        driver.refresh()
        page_load_waiter()
        
        # 少し待ってから確認
        time.sleep(1)
        
        # ログインモーダルが表示されることを確認
        login_modal = driver.find_element(By.ID, "login-modal")
        assert login_modal.value_of_css_property("display") == "block"


class TestLogout:
    """ログアウトパターンのテスト"""
    
    def test_logout_confirmation_dialog(self, driver, page_load_waiter):
        """ログアウトボタンをクリックして確認ダイアログが表示されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # ログイン状態を設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.refresh()
        page_load_waiter()
        
        # ログアウトボタンをクリック
        driver.find_element(By.ID, "auth-button").click()
        
        # 確認ダイアログが表示されることを確認
        WebDriverWait(driver, 2).until(EC.alert_is_present())
    
    def test_logout_removes_tokens(self, driver, page_load_waiter):
        """ログアウト確認後にトークンがlocalStorageから削除されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # ログイン状態を設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.execute_script("localStorage.setItem('oyo_refreshToken', 'mock_refresh_token');")
        driver.refresh()
        page_load_waiter()
        
        # ログアウトボタンをクリックして確認
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
        
        # リロードを待つ
        time.sleep(1.5)
        page_load_waiter()
        
        # トークンが削除されていることを確認
        tokens = driver.execute_script(
            "return {access: localStorage.getItem('oyo_accessToken'), refresh: localStorage.getItem('oyo_refreshToken')}"
        )
        assert tokens['access'] is None
        assert tokens['refresh'] is None
    
    def test_logout_clears_user_display(self, driver, page_load_waiter):
        """ログアウト後にユーザー表示がクリアされることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # ログイン状態を設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        driver.refresh()
        page_load_waiter()
        
        # ログアウトボタンをクリックして確認
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
        
        # リロードを待つ
        time.sleep(1.5)
        page_load_waiter()
        
        # ユーザー表示がクリアされていることを確認
        user_display = driver.find_element(By.ID, "current-user-display").text
        assert user_display == ""
    
    def test_logout_cancel_no_changes(self, driver, page_load_waiter):
        """ログアウトキャンセル時に何も変更されないことを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # ログイン状態を設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.execute_script("localStorage.setItem('oyo_refreshToken', 'mock_refresh_token');")
        driver.refresh()
        page_load_waiter()
        
        # ログアウトボタンをクリックしてキャンセル
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.dismiss()
        
        # トークンが残っていることを確認
        tokens = driver.execute_script(
            "return {access: localStorage.getItem('oyo_accessToken'), refresh: localStorage.getItem('oyo_refreshToken')}"
        )
        assert tokens['access'] == 'mock_access_token'
        assert tokens['refresh'] == 'mock_refresh_token'


class TestSessionPersistence:
    """セッション維持テスト"""
    
    def test_session_persists_after_reload(self, driver, page_load_waiter):
        """ページリロード後もログイン状態が維持されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # ログイン状態を設定
        driver.execute_script("localStorage.setItem('oyo_accessToken', 'mock_access_token');")
        driver.execute_script("localStorage.setItem('oyo_gasConfig', JSON.stringify({url: 'https://script.google.com/macros/s/mock/exec', userId: 'testuser'}));")
        
        mock_gas_api(driver)
        driver.refresh()
        page_load_waiter()
        
        # 少し待ってから確認
        time.sleep(1)
        
        # ユーザー表示が維持されていることを確認
        user_display = driver.find_element(By.ID, "current-user-display").text
        assert "testuser" in user_display
        
        # トークンが維持されていることを確認
        token = driver.execute_script("return localStorage.getItem('oyo_accessToken');")
        assert token == 'mock_access_token'


class TestErrorHandling:
    """エラーハンドリングテスト"""
    
    def test_network_error_message(self, driver, page_load_waiter):
        """ネットワークエラー時に適切なエラーメッセージが表示されることを確認"""
        driver.get(BASE_URL)
        page_load_waiter()
        
        # ネットワークエラーを発生させるモックを設定
        driver.execute_script("""
            window.fetch = async (url, options) => {
                if (url.includes('script.google.com')) {
                    throw new Error('Network error');
                }
                return window.originalFetch(url, options);
            };
        """)
        
        driver.find_element(By.ID, "auth-button").click()
        WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "login-modal")))
        
        driver.find_element(By.ID, "login-user-id").send_keys("testuser")
        driver.find_element(By.ID, "login-password").send_keys("password123")
        driver.find_element(By.ID, "login-button").click()
        
        # エラーメッセージを確認
        WebDriverWait(driver, 5).until(
            lambda d: "通信エラー" in d.find_element(By.ID, "auth-status").text
        )


class TestGASURLConfiguration:
    """GAS URL設定テスト"""
    
    def test_warning_when_gas_url_not_set(self, driver, page_load_waiter):
        """GAS URLが未設定の場合に警告が表示されることを確認"""
        driver.get(BASE_URL)
        
        # GAS設定をクリア
        driver.execute_script("localStorage.removeItem('oyo_gasConfig');")
        driver.refresh()
        
        # 少し待ってから確認
        time.sleep(1)
        
        # 同期モーダルが表示されることを確認
        sync_modal = driver.find_element(By.ID, "sync-modal")
        assert sync_modal.value_of_css_property("display") == "block"
        
        # 警告メッセージを確認
        sync_status = driver.find_element(By.ID, "sync-status")
        assert "GAS URLが設定されていません" in sync_status.text
