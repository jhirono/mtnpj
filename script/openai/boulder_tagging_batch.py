import json
import sys
import os
import time
from openai import OpenAI

def create_batch_jsonl(scraped_data, prompt_text):
    oai_batch_jsonl = scraped_data.replace('.json', '_for_batch.jsonl')
    
    with open(scraped_data, 'r') as f:
        data = json.load(f)
    
    with open(prompt_text, 'r') as f:
        prompt_text = f.read().strip()
    
    with open(oai_batch_jsonl, 'w') as f:
        for area in data:
            for route in area['routes']:
                if 'Boulder' in route['type']:
                    if 'crack' in route['description'] or 'slab' in route['description']:
                        jsonl_entry = {
                            "custom_id": route['route_unique_id'],
                            "method": "POST",
                            "url": "/v1/chat/completions",
                            "body": {
                                "model": "gpt-4o",
                                "messages": [
                                    {"role": "system", "content": prompt_text},
                                    {"role": "user", "content": route['description']}
                                ],
                                "temperature": 1,
                                "max_tokens": 512,
                                "top_p": 1,
                                "frequency_penalty": 0,
                                "presence_penalty": 0
                            }
                        }
                        f.write(json.dumps(jsonl_entry) + "\n")

    print(f"Created {oai_batch_jsonl} for batch processing.")
    return oai_batch_jsonl

def oai_batch_run(batch_input_file):
    client = OpenAI()
    batch_input_file = client.files.create(
        file=open(batch_input_file, 'rb'),
        purpose="batch"
    )
    batch_input_file_id = batch_input_file.id
    batch_job = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata = {
            "description": "Batch job for boulder tagging"
        }
    )

    # Poll the batch job status until it's completed
    while True:
        batch_job = client.batches.retrieve(batch_job.id)  # Refresh the batch job status
        if batch_job.status == "completed":
            break
        elif batch_job.status == "failed":
            print("Batch job failed.")
            exit(1)
        time.sleep(10)  # Wait for 10 seconds before checking again
        print("Polling batch job status...")

    # Retrieve the result
    result_file_id = batch_job.output_file_id
    oai_batch_output = client.files.content(result_file_id)

    # Assuming result is a response object with a binary content attribute
    result_file_name = "batch_job_result.jsonl"
    with open(result_file_name, "wb") as f:
        f.write(oai_batch_output.content)  # Write the binary content to file
    print(f"Batch job result written to {result_file_name}")
    return result_file_name

def update_original_data(scraped_data, oai_batch_output):
    with open(scraped_data, 'r') as f:
        data = json.load(f)
    
    with open(oai_batch_output, 'r') as f:
        batch_data = [json.loads(line) for line in f]
    
    # Create a mapping from custom_id to the desired content
    custom_id_to_content = {}
    for batch_entry in batch_data:
        custom_id = batch_entry['custom_id']
        content = batch_entry['response']['body']['choices'][0]['message']['content']
        custom_id_to_content[custom_id] = content
    
    # Update the original data with the content matched by custom_id
    for area in data:  # Directly iterate through the list
        for route in area['routes']:
            route_unique_id = route['route_unique_id']
            if route_unique_id in custom_id_to_content:
                route['boulder_tags'] = json.loads(custom_id_to_content[route_unique_id])
    
    updated_data = scraped_data.replace('.json', '_boulder_tag.json')
    with open(updated_data, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"Updated data written to {updated_data}.")
    return updated_data

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python trad_protection_tagging_batch.py <scraped_data> <prompt_text>")
        sys.exit(1)
    
    scraped_data = sys.argv[1]
    prompt_text = sys.argv[2]
    
    oai_batch_input = create_batch_jsonl(scraped_data, prompt_text)
    oai_batch_output = oai_batch_run(oai_batch_input)
    updated_data = update_original_data(scraped_data, oai_batch_output)