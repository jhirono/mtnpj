import os
import google.generativeai as genai
import sys

def load_prompt(prompt_file):
    with open(prompt_file, 'r') as file:
        prompt = file.read()
    return prompt

def get_gear_tags(prompt):
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

    response = model.generate_content("TCUs, cams to 2.5 inches or so, set of nuts.  Fixed anchors at the top with rap rings, and you can TR and rap with a 60, but it will be close, so knot the ends of your rope!", safety_settings=safe)
    print(response)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test.py <prompt_file>")
        sys.exit(1)

    prompt_file = sys.argv[1]
    try:
        prompt = load_prompt(prompt_file)
    except FileNotFoundError:
        print(f"Error: The file {prompt_file} was not found.")
        sys.exit(1)

    get_gear_tags(prompt)