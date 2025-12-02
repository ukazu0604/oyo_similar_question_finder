#!/usr/bin/env python3
"""GASにデプロイするスクリプト"""

import subprocess
import sys
import os
import json

def main():
    # gasディレクトリに移動
    gas_dir = os.path.join(os.path.dirname(__file__), 'gas')
    os.chdir(gas_dir)
    
    print("=" * 40)
    print("GASにデプロイ中...")
    print("=" * 40)
    print()
    
    # claspがインストールされているか確認
    try:
        subprocess.run(['C:\\Program Files\\nodejs\\npx.cmd', 'clasp', '--version'], 
                      capture_output=True, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("エラー: claspがインストールされていません。")
        print("以下のコマンドでインストールしてください:")
        print("  npm install -g @google/clasp")
        print()
        sys.exit(1)
    
    # .clasp.jsonが設定されているか確認
    try:
        with open('.clasp.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            if config.get('scriptId') == '<YOUR_SCRIPT_ID>':
                print("エラー: .clasp.jsonにスクリプトIDが設定されていません。")
                print()
                print("以下の手順で設定してください:")
                print("1. GASエディタを開く")
                print("2. プロジェクトの設定 → スクリプトID をコピー")
                print("3. gas\\.clasp.json を開く")
                print("4. <YOUR_SCRIPT_ID> を実際のスクリプトIDに置き換え")
                print()
                sys.exit(1)
    except FileNotFoundError:
        print("エラー: .clasp.jsonが見つかりません。")
        sys.exit(1)
    
    # デプロイ実行
    try:
        subprocess.run(['C:\\Program Files\\nodejs\\npx.cmd', 'clasp', 'push'], check=True)
        print()
        print("=" * 40)
        print("デプロイ完了！")
        print("=" * 40)
    except subprocess.CalledProcessError:
        print()
        print("=" * 40)
        print("デプロイに失敗しました。")
        print("=" * 40)
        print()
        print("ログインしていない場合は、以下のコマンドを実行してください:")
        print("  clasp login")
        sys.exit(1)

if __name__ == '__main__':
    main()
