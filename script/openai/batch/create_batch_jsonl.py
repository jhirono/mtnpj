import json
import sys

def create_jsonl_for_batch_processing(updated_json_file, prompt_file, jsonl_file):
    with open(updated_json_file, 'r') as f:
        data = json.load(f)

    with open(prompt_file, 'r') as f:
        prompt = f.read().strip()

    with open(jsonl_file, 'w') as f:
        for route in data['routes']:
            jsonl_entry = {
                "custom_id": route['unique_id'],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": route['protection']}
                    ],
                    "temperature": 1,
                    "max_tokens": 512,
                    "top_p": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                }
            }
            f.write(json.dumps(jsonl_entry) + "\n")

    print(f"JSONL file for batch processing saved to {jsonl_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_jsonl.py <updated_json_file> <prompt_file> <jsonl_file>")
        sys.exit(1)

    updated_json_file = sys.argv[1]
    prompt_file = sys.argv[2]
    jsonl_file = sys.argv[3]

    create_jsonl_for_batch_processing(updated_json_file, prompt_file, jsonl_file)
