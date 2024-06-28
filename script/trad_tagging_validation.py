import json
import sys
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def load_prompt(prompt_file):
    with open(prompt_file, 'r') as file:
        prompt = file.read()
    return prompt

def get_gear_tags(protection_text, prompt):
    client = openai.Client()
    response = client.chat_completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": protection_text
            }
        ],
        temperature=1,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    completion = response.choices[0].message['content'].strip()
    # Ensure the completion is in JSON list format
    try:
        protection_gear_tags = json.loads(completion)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from completion: {completion}")
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
        expected_output = item['expected_output']
        actual_output = get_gear_tags(input_text, prompt)
        result = {
            'input': input_text,
            'expected_output': expected_output,
            'actual_output': actual_output
        }
        if sorted(actual_output) != sorted(expected_output):
            discrepancies.append(result)
        
        # Write the result to the output file
        output_file = input_file.replace('.jsonl', '_results.jsonl')
        with open(output_file, 'a') as f:
            json.dump(result, f)
            f.write('\n')

    print(f"Processed data saved to {output_file}")
    if discrepancies:
        print(f"Found {len(discrepancies)} discrepancies.")
        for discrepancy in discrepancies:
            print(json.dumps(discrepancy, indent=4))
    else:
        print("No discrepancies found.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python trad-tagging.py <validation_jsonl_file> <prompt_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    prompt_file = sys.argv[2]
    process_json(input_file, prompt_file)
