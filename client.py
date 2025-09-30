from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os

async def main():
    client = MultiServerMCPClient(
        {
            "Calculator":{
                "command": "python",
                "args": ["server/calculator.py"], # check if this path is absolute and correct
                "transport": "stdio",
            },
            "Weather":{
                "url": "http://localhost:8000/mcp", # url for the weather server
                "transport": "streamable_http",
            }
        }
    )
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    tools = await client.get_tools()
    model = ChatGroq(model="llama-3.3-70b-versatile")
    agent = create_react_agent(model, tools)

    math_response = await agent.ainvoke({"messages": [{"role": "user", "content": "What is 10 + ((20 * 30) / 2)?"}]})
    print(f"Math response: {math_response['messages'][-1].content}")

    weather_response = await agent.ainvoke({"messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]})
    print(f"Weather response: {weather_response['messages'][-1].content}")


asyncio.run(main())


