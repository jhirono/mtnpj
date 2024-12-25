import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

client = ChatCompletionsClient(
    endpoint=os.getenv("AZUREAI_ENDPOINT_URL"),
    credential=AzureKeyCredential(os.environ["AZUREAI_ENDPOINT_KEY"])
)

response = client.complete(
    messages=[
        SystemMessage(content="You are a prompt generator for Phi3."),
        UserMessage(content="How many languages are in the world?"),
    ]
)

print(response.choices[0].message.content)