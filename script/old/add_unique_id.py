import json
import sys
import uuid

def add_unique_id(original_json_file, output_json_file):
    with open(original_json_file, 'r') as f:
        data = json.load(f)

    for route in data['routes']:
        route['unique_id'] = str(uuid.uuid4())

    with open(output_json_file, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Added unique IDs to {original_json_file}, saved to {output_json_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_unique_id.py <original_json_file> <output_json_file>")
        sys.exit(1)

    original_json_file = sys.argv[1]
    output_json_file = sys.argv[2]
    add_unique_id(original_json_file, output_json_file)
