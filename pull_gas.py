#!/usr/bin/env python3
"""GASから最新コードを取得するスクリプト"""

import subprocess
import sys
import os

def main():
    # gasディレクトリに移動
    gas_dir = os.path.join(os.path.dirname(__file__), 'gas')
    os.chdir(gas_dir)
    
    print("=" * 40)
    print("GASから最新コードを取得中...")
    print("=" * 40)
    print()
    
    # claspがインストールされているか確認
    try:
        subprocess.run(['clasp', '--version'], 
                      capture_output=True, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("エラー: claspがインストールされていません。")
        print("以下のコマンドでインストールしてください:")
        print("  npm install -g @google/clasp")
        print()
        sys.exit(1)
    
    # 取得実行
    try:
        subprocess.run(['clasp', 'pull'], check=True)
        print()
        print("=" * 40)
        print("取得完了！")
        print("=" * 40)
    except subprocess.CalledProcessError:
        print()
        print("=" * 40)
        print("取得に失敗しました。")
        print("=" * 40)
        sys.exit(1)

if __name__ == '__main__':
    main()
