import os
import google.generativeai as genai
import sys
import json

def load_prompt(prompt_file):
    with open(prompt_file, 'r') as file:
        prompt = file.read()
    return prompt

def get_gear_tags(protection_text, prompt):
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
    model = genai.GenerativeModel(
        model_name='gemini-1.5-pro',
        system_instruction=prompt
    )
    safe = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
    ]

    response = model.generate_content(protection_text, safety_settings=safe)
    
    # Adjusted extraction process based on the response structure
    try: 
        result_content = response.text
        protection_gear_tags = json.loads(result_content)
    except (AttributeError, IndexError, json.JSONDecodeError, TypeError) as e:
        print(f"Error extracting gear tags from response: {e}")
        protection_gear_tags = []
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        print(f"Unexpected error: {e}")
        protection_gear_tags = []    
    return protection_gear_tags

def process_json(input_file, prompt_file):
    with open(prompt_file, 'r') as f:
        prompt = f.read()
    
    with open(input_file, 'r') as f:
        data = [json.loads(line) for line in f]

    discrepancies = []

    for item in data:
        input_text = item['input']
        expected_output = sorted([str(x) for x in item['expected_output']])
        actual_output = sorted([str(x) for x in get_gear_tags(input_text, prompt)])
        result = {
            'input': input_text,
            'expected_output': expected_output,
            'actual_output': actual_output
        }
        if actual_output != expected_output:
            discrepancies.append(result)

    output_file = input_file.replace('.jsonl', '_discrepancies.json')
    with open(output_file, 'w') as f_output:
        json.dump(discrepancies, f_output, indent=4)

    total_inputs = len(data)
    num_discrepancies = len(discrepancies)

    print(f"Processed data saved to {output_file}")
    print(f"Found {num_discrepancies} discrepancies out of {total_inputs} inputs.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python trad_tagging_validation.py <validation_jsonl_file> <prompt_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    prompt_file = sys.argv[2]
    process_json(input_file, prompt_file)