import asyncio
import getpass
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import build_server_config, mcp_server_url

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SYSTEM_PROMPT = (
    "You have MCP tools for math and weather.\n"
    "Use a tool when the user needs exact numbers or current weather—otherwise answer normally.\n"
    "Keep replies short. If a tool errors, say so briefly."
)


def agent_reply_text(result: dict) -> str:
    """Last assistant message text from ``create_agent`` / ``ainvoke`` result."""
    msg = result["messages"][-1]
    c = getattr(msg, "content", None)
    if c is None:
        return str(msg)
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for block in c:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(c)


def fetch_access_token(username: str, password: str) -> str:
    base = mcp_server_url()
    s = requests.Session()
    s.trust_env = False
    r = s.post(
        f"{base}/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=(5, 20),
    )
    r.raise_for_status()
    return str(r.json()["access_token"])


def _token_from_env() -> str | None:
    direct = (os.getenv("MCP_BEARER_TOKEN") or "").strip()
    if direct:
        return direct
    u = (os.getenv("MCP_AUTH_USERNAME") or "").strip()
    p = (os.getenv("MCP_AUTH_PASSWORD") or "").strip()
    if u and p:
        return fetch_access_token(u, p)
    return None


async def build_chat_agent(*, access_token: str | None = None) -> object:
    """LangChain agent over MCP; pass ``access_token`` or set MCP_BEARER_TOKEN / MCP_AUTH_* env."""
    token = (access_token or "").strip() or _token_from_env() or ""
    if not token:
        raise ValueError(
            "Missing MCP token: pass access_token=, or set MCP_BEARER_TOKEN, "
            "or MCP_AUTH_USERNAME + MCP_AUTH_PASSWORD for POST /auth/token."
        )
    client = MultiServerMCPClient(build_server_config(bearer_token=token))
    mcp_tools = await client.get_tools()
    model_groq = ChatGroq(model="llama-3.3-70b-versatile")
    return create_agent(
        model=model_groq,
        tools=mcp_tools,
        system_prompt=SYSTEM_PROMPT,
    )


async def _demo(access_token: str) -> None:
    agent = await build_chat_agent(access_token=access_token)
    print("=======================================================")
    math_response = await agent.ainvoke({"messages": [{"role": "user", "content": "Add amounts 10, 20, 30?"}]})
    print("Math question: Add amounts 10, 20, 30?")
    print(f"Math response: {math_response['messages'][-1].content}")
    print("=======================================================")
    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]}
    )
    print("Weather question: What is the weather in Tokyo?")
    print(f"Weather response: {weather_response['messages'][-1].content}")
    print("=======================================================")


if __name__ == "__main__":
    tok = _token_from_env()
    if not tok:
        u = input(f"MCP server {mcp_server_url()} — username: ").strip()
        p = getpass.getpass("Password: ")
        tok = fetch_access_token(u, p)
    asyncio.run(_demo(tok))
