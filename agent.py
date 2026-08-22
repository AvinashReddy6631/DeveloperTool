import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

response = client.chat.completions.create(
    model="openrouter/free",
    max_tokens=1000,
    messages=[
        {
            "role": "system",
            "content": "You are an AI engineering tutor. MCP means Model Context Protocol, not Minecraft."
        },
        {
            "role": "user",
            "content": "Explain what MCP (Model Context Protocol) is in simple words."
        }
    ]
)

print(response.choices[0].message.content)