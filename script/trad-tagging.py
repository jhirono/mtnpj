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
        model="gpt-4",
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
        data = json.load(f)

    for area in data:
        for route in area['routes']:
            if 'Trad' in route['type']:
                try:
                    route['trad_protection_tags'] = get_gear_tags(route['protection'], prompt)
                    print(f"Processed route {route['route_name']}")
                except Exception as e:
                    print(f"Error processing route {route['route_name']}: {e}")
                    route['trad_protection_tags'] = []
            else:
                route['trad_protection_tags'] = []

    output_file = input_file.replace('.json', '_tagged.json')
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Processed data saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python trad-tagging.py <input_json_file> <prompt_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    prompt_file = sys.argv[2]
    process_json(input_file, prompt_file)
