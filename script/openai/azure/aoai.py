import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("Azure_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint= os.getenv("Azure_OPENAI_ENDPOINT")
)

response = client.chat.completions.create (
    model = "gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Does Azure OpenAI support customer managed keys?"},
        {"role": "assistant", "content": "Yes, customer managed keys are supported by Azure OpenAI."},
        {"role": "user", "content": "Do other Azure AI services support this too?"}
    ]
)

print(response.choices[0].message.content)