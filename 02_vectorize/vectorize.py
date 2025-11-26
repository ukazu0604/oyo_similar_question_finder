"""
応用情報技術者試験 ベクトル化スクリプト

このスクリプトは、ap_siken_all_items.csv を読み込み、
問題名をベクトル化して、ap_siken_all_items_vectors.csv として保存します。
"""

import pandas as pd
import numpy as np
import json
import time
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm
import os

# ========== 設定 ==========
# 使用するモデルを選択
# MODEL_NAME = "pkshatech/GLuCoSE-base-ja"  # 日本語特化モデル
MODEL_NAME = "intfloat/multilingual-e5-large"  # 多言語対応モデル（推奨）
# MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 軽量版

BATCH_SIZE = 32  # バッチサイズ（メモリに応じて調整）
TEXT_COLUMN = "問題名"  # ベクトル化する列名

# ファイルパス
INPUT_FILE = "../01_scraping/ap_siken_all_items.csv"
OUTPUT_DIR = "./output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ap_siken_all_items_vectors.csv")

# ========== メイン処理 ==========
def main():
    # 出力ディレクトリの作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. データの読み込み
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] データを読み込んでいます...")
    print(f"入力ファイル: {INPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"エラー: ファイルが見つかりません: {INPUT_FILE}")
        print(f"現在のディレクトリ: {os.getcwd()}")
        return
    
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] データ読み込み完了: {len(df)}行")
    print(f"\nカラム: {list(df.columns)}")
    print(f"\n最初の3行:")
    print(df.head(3))
    
    # 2. テキストの抽出
    if TEXT_COLUMN not in df.columns:
        raise ValueError(f"エラー: カラム '{TEXT_COLUMN}' が見つかりません。")
    
    texts = df[TEXT_COLUMN].fillna('').tolist()
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] テキスト抽出完了: {len(texts)}件")
    print(f"\nサンプルテキスト:")
    for i, text in enumerate(texts[:3]):
        print(f"{i+1}. {text}")
    
    # 3. モデルのロード
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] モデル '{MODEL_NAME}' をロードしています...")
    print("注意: 初回実行時はモデルのダウンロードが始まります（数分〜数十分かかる場合があります）")
    
    model = SentenceTransformer(MODEL_NAME)
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] モデルのロード完了")
    print(f"ベクトル次元数: {model.get_sentence_embedding_dimension()}")
    
    # 4. ベクトル化の実行
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ベクトル化を開始します...")
    print(f"総テキスト数: {len(texts)}")
    print(f"バッチサイズ: {BATCH_SIZE}")
    
    # ベクトル列名を生成
    vector_column = f"vector_{MODEL_NAME.replace('/', '_').replace('.', '_').replace(':', '_')}"
    print(f"ベクトル列名: {vector_column}")
    
    # バッチ処理でベクトル化
    all_vectors = []
    num_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    
    start_time = time.time()
    
    with tqdm(total=len(texts), desc="ベクトル化中") as pbar:
        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i:i+BATCH_SIZE]
            batch_vectors = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
            all_vectors.extend(batch_vectors)
            pbar.update(len(batch_texts))
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ベクトル化完了")
    print(f"処理時間: {duration:.2f}秒")
    print(f"1件あたり: {duration/len(texts):.3f}秒")
    
    # 5. ベクトルをDataFrameに追加
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ベクトルをDataFrameに追加しています...")
    
    # ベクトルをJSON文字列に変換してDataFrameに追加
    df[vector_column] = [json.dumps(vec.tolist()) for vec in all_vectors]
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 追加完了")
    print(f"\nDataFrameの形状: {df.shape}")
    print(f"カラム数: {len(df.columns)}")
    
    # 6. 結果の保存
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] CSVファイルを保存しています...")
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 保存完了: {OUTPUT_FILE}")
    
    # ファイルサイズを表示
    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"ファイルサイズ: {file_size_mb:.2f} MB")
    
    # 7. 結果の確認
    sample_vector = json.loads(df[vector_column].iloc[0])
    print(f"\nベクトルの次元数: {len(sample_vector)}")
    print(f"\nサンプルベクトル（最初の10次元）:")
    print(sample_vector[:10])
    
    # データの統計情報
    print(f"\n=== 処理結果サマリー ===")
    print(f"総問題数: {len(df)}")
    print(f"使用モデル: {MODEL_NAME}")
    print(f"ベクトル次元数: {len(sample_vector)}")
    print(f"処理時間: {duration:.2f}秒")
    print(f"出力ファイル: {OUTPUT_FILE}")
    print(f"ファイルサイズ: {file_size_mb:.2f} MB")
    
    print("\n完了！")
    print("\n次のステップ:")
    print("1. 03_html_output/main.py を実行して類似度を計算")
    print("2. index.html をブラウザで開いて結果を確認")

if __name__ == "__main__":
    main()
