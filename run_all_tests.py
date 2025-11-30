# -*- coding: utf-8 -*-
"""
==============================================
テスト実行設定
==============================================
設定は test_config.py で一括管理しています
test_config.py を編集してください
==============================================
"""
from test_config import RUN_IN_BACKGROUND, RUN_HEADLESS


import subprocess
import sys
import time
import pytest
import requests
import os
from requests.exceptions import ConnectionError

PORT = 8000
BASE_URL = f"http://localhost:{PORT}/"

# .test_settings.local が存在するかを確認し、存在しなければ作成を促す
CONFIG_FILE_NAME = ".test_settings.local"

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
    # ★ここから追加するロジック★
    if not os.path.exists(CONFIG_FILE_NAME):
        print(f"警告: テスト設定ファイル '{CONFIG_FILE_NAME}' が見つかりません。")
        print(f"テストを開始する前に、まず 'py create_test_config.py' を実行してファイルを作成し、")
        print(f"'{CONFIG_FILE_NAME}' を編集してテスト用のGAS URLを設定してください。")
        sys.exit(1) # テスト実行を中断
    # ★ここまで追加するロジック★

    server_process = None
    server_already_running = False

    # スクリプト自身のディレクトリを取得
    script_dir = os.path.dirname(__file__)

    try:
        # サーバーが起動していることを確認したので、そのままpytestを実行
        print("pytestを実行します...")
        test_files = [
            os.path.join(script_dir, "test_main_page.py"),
            os.path.join(script_dir, "test_ui_interactions.py"),
            os.path.join(script_dir, "test_mobile_view.py"),
            os.path.join(script_dir, "test_auth_sync.py")
        ]
        
        if RUN_IN_BACKGROUND:
            # バックグラウンド実行: subprocessで別プロセスとして起動
            print("🔄 バックグラウンドモードで実行します（すぐに制御が戻ります）")
            # -s を追加して出力を表示
            cmd = [sys.executable, "-m", "pytest", "-v", "-s", "--exitfirst"] + test_files
            subprocess.Popen(
                cmd,
                cwd=script_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            print("✅ テストをバックグラウンドで開始しました")
            print("   結果は別ウィンドウで確認できます")
            sys.exit(0)
        else:
            # フォアグラウンド実行: 従来通りpytest.mainで実行
            print("⏳ フォアグラウンドモードで実行します（完了まで待機）")
            # -s を追加して出力を表示
            exit_code = pytest.main(["-v", "-s", "--exitfirst"] + test_files)

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

