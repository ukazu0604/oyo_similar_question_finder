import subprocess
import os
import yaml

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '../02_vectorize/config.yaml')
    
    config = load_config(config_path)
    models = config.get('models', [])
    
    generated_models = []

    for model in models:
        model_name = model['name']
        print(f"Generating JSON for model: {model_name}...")
        
        # モデル名からファイル名を生成 (例: similar_results_ruri.json)
        # '/' や ':' などを '_' に置換し、小文字化
        safe_name = model_name.split('/')[-1].replace('-', '_').replace('.', '_').lower()
        if 'gemini' in model_name or 'text-embedding' in model_name:
             safe_name = 'gemini'
        elif 'e5' in model_name:
             safe_name = 'e5'
        elif 'ruri' in model_name:
             safe_name = 'ruri'
             
        output_filename = f"similar_results_{safe_name}.json"
        
        import sys
        cmd = [
            sys.executable, "main.py",
            "--model", model_name,
            "--output_filename", output_filename
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=script_dir)
            print(f"Successfully generated {output_filename}")
            generated_models.append({
                "id": output_filename,
                "name": model_name
            })
        except subprocess.CalledProcessError as e:
            print(f"Error generating {output_filename}: {e}")

    # Generate models.json manifest
    import json
    models_json_path = os.path.join(script_dir, '../03_html_output/models.json')
    # Ensure the directory exists (it should, but just in case)
    os.makedirs(os.path.dirname(models_json_path), exist_ok=True)
    
    with open(models_json_path, 'w', encoding='utf-8') as f:
        json.dump(generated_models, f, indent=2, ensure_ascii=False)
    print(f"Generated models manifest at {models_json_path}")

if __name__ == "__main__":
    main()
