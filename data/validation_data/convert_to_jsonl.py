import json
import sys
import os

if len(sys.argv) != 2:
    print("Usage: python convert_to_jsonl.py <input_file>")
    sys.exit(1)

input_file = sys.argv[1]
base_name = os.path.splitext(input_file)[0]
output_file = f'{base_name}_validation_data.jsonl'

try:
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        input_text = None
        for line in lines:
            line = line.strip()
            if line.startswith("input:"):
                input_text = line.replace("input: ", "").strip()
            elif line.startswith("output:"):
                output_text = line.replace("output: ", "").strip()
                if input_text is not None:
                    data = {
                        "input": input_text,
                        "expected_output": [item.strip() for item in output_text.split(',')]
                    }
                    json.dump(data, outfile)
                    outfile.write('\n')
                input_text = None
except FileNotFoundError:
    print(f"Error: The file {input_file} was not found.")
    sys.exit(1)

print(f"Conversion complete. The JSONL file has been saved as {output_file}.")