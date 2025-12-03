import json
import os

def main():
    with open('gen_log.txt', 'w') as log:
        log.write("Script started\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    json_path = os.path.join(script_dir, 'problem_data.js')
    template_path = os.path.join(project_root, 'index_template.html')
    output_path = os.path.join(project_root, 'index.html')
    
    print(f"Reading JSON from: {json_path}")
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Extract JSON string from "window.PROBLEM_DATA = {json};"
        json_start = js_content.find('{')
        json_end = js_content.rfind('}') + 1
        json_str = js_content[json_start:json_end]
        
        data = json.loads(json_str)
        
        # Add model name explicitly if missing
        if 'model' not in data or not data['model']:
            # Try to get model name from problem_data.js filename
            filename_model = os.path.basename(json_path).replace('problem_data_', '').replace('.js', '')
            if filename_model:
                data['model'] = filename_model
            else:
                data['model'] = 'Unknown Model'
            
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    print(f"Reading template from: {template_path}")
    if not os.path.exists(template_path):
        print(f"Error: Template file not found at {template_path}")
        return

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template: {e}")
        return

    # Embed data
    embedding_script = f'<script>window.PROBLEM_DATA = {json_str};</script>'
    output_content = template_content.replace('<!-- DATA_PLACEHOLDER -->', embedding_script)
    
    print(f"Writing output to: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print("Successfully generated index.html with embedded data.")
    except Exception as e:
        print(f"Error writing output: {e}")

if __name__ == '__main__':
    main()
