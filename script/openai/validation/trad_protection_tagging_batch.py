import json
import sys
import os
import uuid
import time
from openai import OpenAI

def convert_to_jsonl(input_file):
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
    
    return output_file

def create_jsonl_for_batch_processing(output_file, prompt_file):
    # Derive jsonl_file name from output_file name
    base_name = os.path.splitext(output_file)[0]
    jsonl_file = f"{base_name}_processed.jsonl"

    # Read the prompt file once
    with open(prompt_file, 'r') as f:
        prompt = f.read().strip()

    # Process the output_file and write to jsonl_file
    with open(output_file, 'r') as input_f, open(jsonl_file, 'w') as output_f:
        for line in input_f:
            route_data = json.loads(line)  # Parse each line to a dict

            # Add required fields
            jsonl_entry = {
                "custom_id": str(uuid.uuid4()),
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": route_data['input']}
                    ],
                    "temperature": 1,
                    "max_tokens": 512,
                    "top_p": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                }
            }

            # Write the modified entry to the new JSONL file
            output_f.write(json.dumps(jsonl_entry) + "\n")
    
    return jsonl_file

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
            "description": "Batch of routes from the Upper Castle"
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
        time.sleep(3)  # Wait for 10 seconds before checking again
        print("Polling batch job status...")

    # Retrieve the result
    result_file_id = batch_job.output_file_id
    result = client.files.content(result_file_id)

    # Assuming result is a response object with a binary content attribute
    result_file_name = "batch_job_result.jsonl"
    with open(result_file_name, "wb") as f:
        f.write(result.content)  # Write the binary content to file
    print(f"Batch job result written to {result_file_name}")
    return result

def validation(validation_file, batch_output_file):
    with open(validation_file, 'r') as f:
        validation_data = [json.loads(line) for line in f]
    
    with open(batch_output_file, 'r') as f:
        batch_data = [json.loads(line) for line in f]

    discrepancies = []

    for validation_item, batch_item in zip(validation_data, batch_data):
        input_text = validation_item['input']
        expected_output = sorted([str(x) for x in validation_item['expected_output']])
        actual_output = sorted([str(x) for x in batch_item['choices'][0]['message']['content']])
        result = {
            'input': input_text,
            'expected_output': expected_output,
            'actual_output': actual_output
        }
        if actual_output != expected_output:
            discrepancies.append(result)

    output_file = validation_file.replace('.jsonl', '_discrepancies.json')
    with open(output_file, 'w') as f:
        for item in discrepancies:
            f.write(json.dumps(item) + '\n')
    
    print(f"Discrepancies saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <prompt_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    prompt_file = sys.argv[2]
    validation_file = convert_to_jsonl(input_file)
    batch_input_file = create_jsonl_for_batch_processing(validation_file, prompt_file)
    batch_output_file = oai_batch_run(batch_input_file)
    validation(validation_file, batch_output_file)
