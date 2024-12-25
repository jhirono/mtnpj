import json
import sys
import os
import uuid
import time
from openai import OpenAI

def convert_text_validation_data_to_jsonl(input_file):
    base_name = os.path.splitext(os.path.basename(input_file))[0]  # Use basename to get the file name without the path
    output_file = f'data/validation_data/{base_name}_validation_data.jsonl'  # Specify the directory

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
                        custom_id = str(uuid.uuid4())
                        data = {
                            "input": input_text,
                            "expected_output": [item.strip() for item in output_text.split(',')],
                            "custom_id": custom_id
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
    oai_batch_input = f"{base_name}_processed_for_batch.jsonl"

    # Read the prompt file once
    with open(prompt_file, 'r') as f:
        prompt = f.read().strip()

    # Process the output_file and write to jsonl_file
    with open(output_file, 'r') as input_f, open(oai_batch_input, 'w') as output_f:
        for line in input_f:
            route_data = json.loads(line)  # Parse each line to a dict

            # Add required fields
            jsonl_entry = {
                "custom_id": route_data['custom_id'],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
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

    return oai_batch_input

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
            "description": "Batch job for trad protection tagging"
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
    oai_batch_output = client.files.content(result_file_id)

    # Assuming result is a response object with a binary content attribute
    result_file_name = "batch_job_result.jsonl"
    with open(result_file_name, "wb") as f:
        f.write(oai_batch_output.content)  # Write the binary content to file
    print(f"Batch job result written to {result_file_name}")
    return result_file_name

def validation(oai_batch_input, oai_batch_output):
    # Convert batch_output to a dictionary for easier access by custom_id
    batch_data_dict = {}
    discrepancies = []

    # Read and parse the oai_batch_output jsonl file
    with open(oai_batch_output, 'r') as output_file:
        for line in output_file:
            item = json.loads(line)
            batch_data_dict[item['custom_id']] = item

    # Read and validate each item in the oai_batch_input jsonl file
    with open(oai_batch_input, 'r') as input_file:
        for line in input_file:
            validation_item = json.loads(line)
            custom_id = validation_item['custom_id']
            input = validation_item['input']
            if custom_id in batch_data_dict:
                batch_item = batch_data_dict[custom_id]
                expected_output = sorted([str(x) for x in validation_item.get('expected_output', [])])
                actual_output_content = batch_item['response']['body']['choices'][0]['message']['content']
                try:
                    actual_output = sorted([str(x) for x in json.loads(actual_output_content)])
                except json.JSONDecodeError:
                    print(f"Error decoding JSON for custom_id {custom_id}")
                    continue
                if actual_output != expected_output:
                    discrepancies.append({
                        'custom_id': custom_id,
                        'input': input,
                        'expected_output': expected_output,
                        'actual_output': actual_output
                    })
    with open('discrepancies.json', 'w') as f:
        json.dump(discrepancies, f, indent=4)
    return discrepancies

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <prompt_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    prompt_file = sys.argv[2]
    validation_file = convert_text_validation_data_to_jsonl(input_file)
    batch_input_file = create_jsonl_for_batch_processing(validation_file, prompt_file)
    batch_output_file = oai_batch_run(batch_input_file)
    discrepancies = validation(validation_file, batch_output_file)
    print(json.dumps(discrepancies, indent=4))