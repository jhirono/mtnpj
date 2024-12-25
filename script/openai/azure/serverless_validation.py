import json
import sys
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

def load_prompt(prompt_file):
    with open(prompt_file, 'r') as file:
        prompt = file.read()
    return prompt

def get_gear_tags(protection_text, prompt):
    client = ChatCompletionsClient(
    endpoint=os.getenv("AZUREAI_ENDPOINT_URL"),
    credential=AzureKeyCredential(os.environ["AZUREAI_ENDPOINT_KEY"])
    )

    response = client.complete(
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

    completion = response.choices[0].message.content
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