import pandas as pd
import numpy as np
import json
import os
import argparse
import yaml
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from tqdm import tqdm

def print_log(message):
    print(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def load_config(config_path):
    """設定ファイルを読み込む。スクリプトの場所を基準にパスを解決する。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_config_path = os.path.normpath(os.path.join(script_dir, config_path))
    print_log(f"設定ファイル '{absolute_config_path}' の読み込みを開始します...")
    if not os.path.exists(absolute_config_path):
        print_log(f"エラー: 設定ファイルが見つかりません: {absolute_config_path}")
        return None
    with open(absolute_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print_log("設定ファイルの読み込みが完了しました。")
    return config

def extract_vector(value):
    if pd.isna(value) or value == '' or value == 'None' or value == '[]':
        return None
    try:
        v = json.loads(value)
        if isinstance(v, list) and len(v) > 0:
            return np.array(v)
    except:
        pass
    return None

def get_vector_column_name(model_config):
    model_name = model_config.get('name')
    if model_name == 'embeddinggemma':
        return 'embedding'
        
    model_type = model_config.get('type')
    if model_type == 'sentence-transformers' and 'huggingface_name' in model_config:
        name_to_use = model_config['huggingface_name']
    else:
        name_to_use = model_config['name']
    return f"vector_{name_to_use.replace('/', '_').replace('.', '_').replace(':', '_').replace('-', '_')}"

def select_output_data(data_dict):
    """JSONに出力するデータを選択する"""
    # ベクトル列を除いた、表示に必要なデータだけを返す
    required_keys = ['大項目', '中項目', '問題番号', '問題名', 'リンク', '出典']
    return {key: data_dict.get(key) for key in required_keys}

def compute_similarities(df, vector_column):
    grouped = defaultdict(list)
    for idx, row in df.iterrows():
        mid = row['中項目']
        vector = extract_vector(row[vector_column])
        if vector is not None:
            grouped[mid].append({'index': idx, 'vector': vector, 'data': row.to_dict()})

    # 結果を格納する辞書を準備
    results = {
        "model": None, # 後でモデル名を設定
        "categories": {}
    }

    for middle_cat, items in tqdm(grouped.items(), desc="類似度計算中"):
        if len(items) < 2:
            continue
        vectors = np.array([x['vector'] for x in items])
        sim_matrix = cosine_similarity(vectors)
        category_results = []

        for i, item in enumerate(items):
            sims = []
            for j, score in enumerate(sim_matrix[i]):
                if i != j:
                    # 類似度90%以上をすべて抽出
                    if float(score) >= 0.9:
                        sims.append({
                            "similarity": float(score),
                            "data": select_output_data(items[j]['data'])
                        })
            sims.sort(key=lambda x: x['similarity'], reverse=True)
            category_results.append({
                "main_problem": select_output_data(item['data']),
                "similar_problems": sims  # 全件出力 (閾値判定済み)
            })
        results["categories"][middle_cat] = category_results

    return results

def main():
    parser = argparse.ArgumentParser(description="類似度JSONを生成します。")
    # デフォルトパスをスクリプトからの相対パスとして定義
    parser.add_argument('--csv_path', type=str, default='../02_vectorize/output/ap_siken_all_items_vectors.csv', help='ベクトル化済みCSVファイルのパス')
    parser.add_argument('--config_path', type=str, default='../02_vectorize/config.yaml', help='config.yamlのパス')
    parser.add_argument('--output_dir', type=str, default='../03_html_output', help='JSONの出力先ディレクトリ')
    parser.add_argument('--model', type=str)
    parser.add_argument('--output_filename', type=str, default='problem_data.js', help='出力JSファイル名')
    args = parser.parse_args()

    print_log("=== 類似問題JS生成開始 ===")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.normpath(os.path.join(script_dir, args.csv_path))
    output_dir = os.path.normpath(os.path.join(script_dir, args.output_dir))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, args.output_filename)

    config = load_config(args.config_path)
    if config is None: return

    models_config = config.get('models', [])
    if not models_config:
        print_log("config.yamlにmodelsがありません。")
        return
    
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    required = ['大項目', '中項目', '問題番号', '問題名', 'リンク', '出典']
    for col in required:
        if col not in df.columns:
            print_log(f"エラー: {col} 列が存在しません")
            return

    if args.model:
        model_config = next((m for m in models_config if m['name'] == args.model), None)
    else:
        model_config = models_config[0]

    model_name = model_config['name']
    vector_column = get_vector_column_name(model_config)

    print_log(f"使用モデル: {model_name}")

    results = compute_similarities(df, vector_column)
    results['model'] = model_name # 結果に使用したモデル名を追加

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("window.PROBLEM_DATA = ")
        json.dump(results, f, ensure_ascii=False, indent=2)
        f.write(";")

    print_log(f"JS出力完了: {output_path}")
    print_log("=== 完了 ===")

if __name__ == '__main__':
    main()
