import os

CONFIG_FILE_NAME = ".test_settings.local"
DEFAULT_CONTENT = """\
# このファイルは.gitignoreで無視されます。
# テスト用のGAS URLをここに設定してください。
# 例: TEST_GAS_URL = "https://script.google.com/macros/s/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/exec"
TEST_GAS_URL = "https://script.google.com/macros/s/YOUR_TEST_GAS_URL_HERE/exec"
"""

def create_config_file():
    if os.path.exists(CONFIG_FILE_NAME):
        print(f"'{CONFIG_FILE_NAME}'は既に存在します。上書きしますか？ (y/N): ", end='')
        response = input().strip().lower()
        if response != 'y':
            print("ファイルの作成をスキップしました。")
            return

    try:
        with open(CONFIG_FILE_NAME, "w") as f:
            f.write(DEFAULT_CONTENT)
        print(f"'{CONFIG_FILE_NAME}'を作成しました。")
        print("ファイルを開き、TEST_GAS_URLを適切な値に設定してください。")
        
        # .gitignoreに追記する案内
        gitignore_path = ".gitignore"
        with open(gitignore_path, "a+") as f:
            f.seek(0)
            content = f.read()
            if CONFIG_FILE_NAME not in content:
                f.write(f"\n# Ignore local test settings\n{CONFIG_FILE_NAME}\n")
                print(f"'{CONFIG_FILE_NAME}'を.gitignoreに追加しました。")
            else:
                print(f"'{CONFIG_FILE_NAME}'は既に.gitignoreに記述されています。")

    except IOError as e:
        print(f"ファイルの作成中にエラーが発生しました: {e}")

if __name__ == "__main__":
    create_config_file()
