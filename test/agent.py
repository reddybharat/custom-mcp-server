from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from config import server_config

from dotenv import load_dotenv
load_dotenv()

import asyncio

SYSTEM_PROMPT = (
    "You have MCP tools for math, weather, bank transactions, and trades.\n"
    "Use a tool when the user needs exact numbers, weather, transactions for a date range, "
    "or trade details for a reference number—otherwise answer normally.\n"
    "Keep replies short. If a tool errors, say so briefly."
)


async def build_chat_agent():
    """Create the LangChain agent wired to configured MCP servers."""
    client = MultiServerMCPClient(server_config)
    mcp_tools = await client.get_tools()
    model_groq = ChatGroq(model="llama-3.3-70b-versatile")
    return create_agent(
        model=model_groq,
        tools=mcp_tools,
        system_prompt=SYSTEM_PROMPT,
    )


async def main():
    agent = await build_chat_agent()

    print("=======================================================")
    math_response = await agent.ainvoke({"messages": [{"role": "user", "content": "Add amounts 10, 20, 30?"}]})
    print(f"Math question: Add amounts 10, 20, 30?")
    print(f"Math response: {math_response['messages'][-1].content}")
    print("=======================================================")
    weather_response = await agent.ainvoke({"messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]})
    print(f"Weather question: What is the weather in Tokyo?")
    print(f"Weather response: {weather_response['messages'][-1].content}")
    print("=======================================================")


if __name__ == "__main__":
    asyncio.run(main())
