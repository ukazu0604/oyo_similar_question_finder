import pandas as pd
import numpy as np
import json
import os
import argparse
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from tqdm import tqdm

def print_log(message):
    print(f"[{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

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
        vector = row[vector_column]
        if vector is not None and len(vector) > 0:
            grouped[mid].append({'index': idx, 'vector': np.array(vector), 'data': row.to_dict()})

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
                    sims.append({
                        "similarity": float(score),
                        "data": select_output_data(items[j]['data'])
                    })
            
            # Sort by similarity descending
            sims.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Filter: Top 5 OR Similarity >= 0.9
            filtered_sims = []
            for idx, sim in enumerate(sims):
                if idx < 5 or sim['similarity'] >= 0.9:
                    filtered_sims.append(sim)
            
            category_results.append({
                "main_problem": select_output_data(item['data']),
                "similar_problems": filtered_sims
            })
        results["categories"][middle_cat] = category_results

    return results

def main():
    parser = argparse.ArgumentParser(description="類似度JSONを生成します。")
    # デフォルトパスをスクリプトからの相対パスとして定義
    parser.add_argument('--input_json', type=str, default='gemma_embeddings.json', help='入力JSONファイルのパス')
    parser.add_argument('--output_dir', type=str, default='../03_html_output', help='JSONの出力先ディレクトリ')
    parser.add_argument('--output_filename', type=str, default='problem_data.js', help='出力JSファイル名')
    args = parser.parse_args()

    print_log("=== 類似問題JS生成開始 ===")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_json_path = os.path.normpath(os.path.join(script_dir, args.input_json))
    output_dir = os.path.normpath(os.path.join(script_dir, args.output_dir))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, args.output_filename)

    # Hardcode the model configuration for embeddinggemma
    # Since we are standardizing on gemma and not using multiple models
    models_config = [
        {
            "name": "embeddinggemma",
            "type": "ollama",
            "timeout": 36000 # Dummy value, not actually used by this script
        }
    ]
    
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    required = ['大項目', '中項目', '問題番号', '問題名', 'リンク', '出典']
    for col in required:
        if col not in df.columns:
            print_log(f"エラー: {col} 列が存在しません")
            return

    model_config = next((m for m in models_config if m['name'] == 'embeddinggemma'), None)
    if not model_config:
        print_log("config.yamlにembeddinggemmaモデルが見つかりません。")
        return

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
