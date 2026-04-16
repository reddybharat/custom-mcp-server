from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os

async def main():
    client = MultiServerMCPClient(
        {
            "Math":{
                "command": "python",
                "args": ["server/math.py"],
                "transport": "stdio",
            },
            "Weather":{
                "url": "http://localhost:8000/mcp", # url for the weather server
                "transport": "streamable_http",
            }
        }
    )
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    MCP_TOOLS = await client.get_tools()

    model_groq = ChatGroq(model="llama-3.3-70b-versatile")

    system_prompt = (
        "You are an assistant with tools from MCP servers (math and weather).\n\n"
        "Rules:\n"
        "- For arithmetic, formulas, or any question that needs exact numeric computation: "
        "call the math tools. Prefer tools over doing the calculation yourself.\n"
        "- For current weather, temperature, or conditions for a city or location: "
        "call the weather tools with that location.\n"
        "- Use only the tools that fit the question. If both apply, call tools in a sensible order.\n"
        "- After you receive tool results, reply in short, plain language. "
        "If a tool fails, say so briefly and suggest what to check (e.g. location spelling, server running)."
    )

    agent = create_agent(
        model=model_groq,
        tools=MCP_TOOLS,
        system_prompt=system_prompt,
    )

    print("=======================================================")
    math_response = await agent.ainvoke({"messages": [{"role": "user", "content": "What is 10 + ((20 * 30) / 2)?"}]})
    print(f"Math question: What is 10 + ((20 * 30) / 2)?")
    print(f"Math response: {math_response['messages'][-1].content}")
    print("=======================================================")
    weather_response = await agent.ainvoke({"messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]})
    print(f"Weather question: What is the weather in Tokyo?")
    print(f"Weather response: {weather_response['messages'][-1].content}")
    print("=======================================================")


asyncio.run(main())


