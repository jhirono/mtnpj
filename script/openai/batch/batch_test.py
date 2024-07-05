from openai import OpenAI
import json
import os
import time
import sys

if len(sys.argv) < 2:
    print("Usage: python3 batch_test.py <input_jsonl_file_path>")
    sys.exit(1)

input_jsonl_file_path = sys.argv[1]

client = OpenAI()

batch_input_file = client.files.create(
    file=open(input_jsonl_file_path, 'rb'),
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
    time.sleep(10)  # Wait for 10 seconds before checking again

# Retrieve the result
result_file_id = batch_job.output_file_id
result = client.files.content(result_file_id)

# Assuming result is a response object with a binary content attribute
result_file_name = "batch_job_result.jsonl"
with open(result_file_name, "wb") as f:
    f.write(result.content)  # Write the binary content to file
print(f"Batch job result written to {result_file_name}")