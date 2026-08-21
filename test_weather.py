import asyncio
from weather_agent import weather_agent

result = asyncio.run(
    weather_agent("What is the weather in Hyderabad?")
)

print(result)