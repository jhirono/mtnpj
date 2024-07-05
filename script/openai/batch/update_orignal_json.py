import json
import sys

def update_json_with_gpt_output(original_json_file, gpt_output_file, updated_json_file):
    with open(original_json_file, 'r') as f:
        data = json.load(f)

    with open(gpt_output_file, 'r') as f:
        gpt_responses = [json.loads(line) for line in f]

    # Create a mapping from custom_id to GPT output
    gpt_output_map = {}
    for response in gpt_responses:
        custom_id = response['custom_id']
        gpt_output_raw = response['response']['body']['choices'][0]['message']['content']
        
        # Parse the gpt_output_raw string to convert it into a Python list
        try:
            gpt_output_list = json.loads(gpt_output_raw)
        except json.JSONDecodeError:
            print(f"Error decoding JSON for custom_id {custom_id}: {gpt_output_raw}")
            continue
        
        # Store the list for later use
        gpt_output_map[custom_id] = gpt_output_list

    # Update the original JSON data with the GPT output
    for route in data['routes']:
        route_id = route['unique_id']
        if route_id in gpt_output_map:
            # Assign the parsed list directly to the trad_protection_tags field
            route['trad_protection_tags'] = gpt_output_map[route_id]

    # Write the updated JSON data to a new file
    with open(updated_json_file, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Updated JSON file saved to {updated_json_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python update_original_json.py <original_json_file> <gpt_output_file> <updated_json_file>")
        sys.exit(1)

    original_json_file = sys.argv[1]
    gpt_output_file = sys.argv[2]
    updated_json_file = sys.argv[3]

    update_json_with_gpt_output(original_json_file, gpt_output_file, updated_json_file)