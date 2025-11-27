import subprocess
import sys
import time
import pytest
import requests
import os
from requests.exceptions import ConnectionError

PORT = 8000
BASE_URL = f"http://localhost:{PORT}/"

def wait_for_server(timeout=15):
    """サーバーが起動して応答するまで待機する。"""
    print(f"サーバー ({BASE_URL}) の起動を待っています...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(BASE_URL)
            if response.status_code == 200:
                print("サーバーが起動しました。テストを開始します。")
                return True
        except ConnectionError:
            time.sleep(0.5)  # 0.5秒待ってから再試行
    print(f"エラー: {timeout}秒以内にサーバーが起動しませんでした。")
    return False

def main():
    """
    Webサーバーの起動、pytestの実行、サーバーの停止を順番に行う。
    サーバーが既に起動している場合は、それを利用してテストを実行する。
    """
    server_process = None
    server_already_running = False

    # スクリプト自身のディレクトリを取得
    script_dir = os.path.dirname(__file__)

    # 最初にサーバーが起動しているかチェック
    try:
        requests.get(BASE_URL, timeout=1)
        print("既存のサーバーが起動していることを検出しました。")
        print("このサーバーに対してテストを実行します。テスト後にサーバーは停止されません。")
        server_already_running = True
    except ConnectionError:
        print("エラー: サーバーが起動していません。テストを実行できません。")
        sys.exit(1) # サーバーが起動していない場合は終了

    try:
        # サーバーが起動していることを確認したので、そのままpytestを実行
        print("pytestを実行します...")
        test_files = [
            os.path.join(script_dir, "test_main_page.py"),
            os.path.join(script_dir, "test_ui_interactions.py"),
            os.path.join(script_dir, "test_mobile_view.py")
        ]
        exit_code = pytest.main(["-v"] + test_files)

        # 4. スクリプト全体の終了コードをpytestの結果に合わせる
        if exit_code != 0:
            print(f"テストでエラーが検出されました。終了コード: {exit_code}")
            sys.exit(exit_code)
        else:
            print("すべてのテストが成功しました。")

    finally:
        # サーバーは自動起動していないため、停止処理は不要
        pass

if __name__ == "__main__":
    main()
