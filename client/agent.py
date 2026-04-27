import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

from client.config import build_server_config, mcp_server_url

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
    try:
        r = s.post(
            f"{base}/auth/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=(5, 20),
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Could not reach MCP server at {base}: {e}") from e

    if r.status_code == 401:
        raise ValueError(
            "Invalid username or password. Please check your credentials and try again."
        )
    if not r.ok:
        detail = ""
        try:
            body = r.json()
            d = body.get("detail")
            if isinstance(d, str):
                detail = d
            elif d is not None:
                detail = str(d)
        except Exception:
            detail = (r.text or "")[:200]
        raise RuntimeError(
            f"Authentication request failed (HTTP {r.status_code}). {detail or r.reason}".strip()
        )
    try:
        return str(r.json()["access_token"])
    except (KeyError, ValueError) as e:
        raise RuntimeError("Unexpected response from server: missing access_token.") from e


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


async def _run_single_query(*, access_token: str, query: str) -> str:
    agent = await build_chat_agent(access_token=access_token)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    return agent_reply_text(result)


def _parse_cli_query() -> str:
    parser = argparse.ArgumentParser(
        description="Authenticate to the MCP API, then ask the agent one question."
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Question for the agent (if omitted, you will be prompted)",
    )
    args = parser.parse_args()
    q = " ".join(args.query).strip()
    if not q:
        q = input("Question: ").strip()
    return q


# From repo root: python -m client.agent "your question"  — or no args to be prompted for the question.
if __name__ == "__main__":
    query = _parse_cli_query()
    if not query:
        print("Error: empty question.", file=sys.stderr)
        sys.exit(1)

    try:
        tok = _token_from_env()
        if not tok:
            u = input(f"MCP server {mcp_server_url()} — username: ").strip()
            p = getpass.getpass("Password: ")
            tok = fetch_access_token(u, p)
    except (ValueError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    try:
        reply = asyncio.run(_run_single_query(access_token=tok, query=query))
    except Exception as e:
        print(f"Agent error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Response: {reply}")
