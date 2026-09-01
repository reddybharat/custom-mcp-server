import argparse
import asyncio
import getpass
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

from client.config import build_server_config, build_single_server_config, mcp_server_url
from client.mcp_context import mcp_bootstrap_system_extension, selective_mcp_context

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "You have MCP tools for math and weather.\n"
    "Use a tool when the user needs exact numbers or current weather—otherwise answer normally.\n"
    "Keep replies short. If a tool errors, say so briefly."
)


@dataclass(frozen=True)
class MCPAgentBundle:
    """LangChain agent plus the MCP client used for prompts/resources (selective context per turn)."""

    agent: object
    client: MultiServerMCPClient


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


def format_mcp_auth_error(exc: Exception) -> str | None:
    """Map MCP HTTP auth failures to clear 401/503 messages."""
    text = f"{type(exc).__name__}: {exc}"
    lower = text.lower()
    if re.search(r"\b503\b", text) or "not configured" in lower:
        return "MCP server not configured (503): MCP API key not configured on server"
    if re.search(r"\b401\b", text) or "unauthorized" in lower or "invalid or missing api key" in lower:
        return "MCP auth failed (401): Invalid or missing API key"
    return None


def _api_key_from_env() -> str | None:
    key = (os.getenv("MCP_API_KEY") or "").strip()
    return key or None


def groq_model() -> str:
    return (os.getenv("GROQ_MODEL") or DEFAULT_GROQ_MODEL).strip()


def resolve_api_key(*, cli_api_key: str | None = None, prompt: bool = True) -> str:
    """Resolve API key: CLI flag → env → optional getpass."""
    if cli_api_key and cli_api_key.strip():
        return cli_api_key.strip()
    env_key = _api_key_from_env()
    if env_key:
        return env_key
    if not prompt:
        raise ValueError(
            "Missing MCP API key: pass --api-key, or set MCP_API_KEY in the environment."
        )
    return getpass.getpass(f"MCP server {mcp_server_url()} — API key: ").strip()


async def build_chat_agent(
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    mcp_url: str | None = None,
) -> MCPAgentBundle:
    """LangChain agent over MCP; pass ``api_key`` or set ``MCP_API_KEY`` env.

  ``mcp_url`` connects to one MCP endpoint (Streamlit). ``base_url`` connects to
    all default mounts (CLI). MCP prompts/resources are merged into the system
    prompt at build time; keep ``bundle.client`` for per-turn ``selective_mcp_context``.
    """
    key = (api_key or "").strip() or _api_key_from_env() or ""
    if not key:
        raise ValueError(
            "Missing MCP API key: pass api_key=, set MCP_API_KEY, or use --api-key / getpass."
        )
    if mcp_url and mcp_url.strip():
        config = build_single_server_config(mcp_url=mcp_url.strip(), api_key=key)
    else:
        config = build_server_config(api_key=key, base_url=base_url)
    client = MultiServerMCPClient(config)
    try:
        mcp_tools = await client.get_tools()
        mcp_extra = await mcp_bootstrap_system_extension(client)
    except Exception as exc:
        auth_msg = format_mcp_auth_error(exc)
        if auth_msg:
            raise RuntimeError(auth_msg) from exc
        raise
    system = SYSTEM_PROMPT
    if mcp_extra:
        system = f"{SYSTEM_PROMPT}\n\n---\nMCP bootstrap (prompts, resources, discovery):\n{mcp_extra}"
    model_groq = ChatGroq(model=groq_model())
    agent = create_agent(
        model=model_groq,
        tools=mcp_tools,
        system_prompt=system,
    )
    return MCPAgentBundle(agent=agent, client=client)


async def ainvoke_with_selective_mcp(
    bundle: MCPAgentBundle,
    messages: list[dict[str, str]],
) -> dict:
    """Run the agent after optionally appending turn-specific MCP prompt text to the last user turn."""
    if not messages:
        return await bundle.agent.ainvoke({"messages": messages})
    extra = await selective_mcp_context(bundle.client, str(messages[-1].get("content", "")))
    if not extra:
        return await bundle.agent.ainvoke({"messages": messages})
    msgs = messages.copy()
    last = msgs[-1]
    if last.get("role") == "user":
        msgs[-1] = {**last, "content": f"{last.get('content', '')}\n\n{extra}"}
    else:
        msgs.append({"role": "user", "content": extra})
    return await bundle.agent.ainvoke({"messages": msgs})


async def _run_single_query(*, api_key: str, query: str) -> str:
    bundle = await build_chat_agent(api_key=api_key)
    result = await ainvoke_with_selective_mcp(
        bundle, [{"role": "user", "content": query}]
    )
    return agent_reply_text(result)


def _parse_cli_args() -> tuple[str | None, str]:
    parser = argparse.ArgumentParser(
        description="Connect to the MCP API with an API key, then ask the agent one question."
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=None,
        help="MCP API key (overrides MCP_API_KEY env)",
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
    return args.api_key, q


# From repo root: python -m client.agent "your question"  — or no args to be prompted for the question.
if __name__ == "__main__":
    cli_api_key, query = _parse_cli_args()
    if not query:
        print("Error: empty question.", file=sys.stderr)
        sys.exit(1)

    try:
        key = resolve_api_key(cli_api_key=cli_api_key, prompt=True)
        if not key:
            raise ValueError("Empty API key.")
    except (ValueError, RuntimeError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    try:
        reply = asyncio.run(_run_single_query(api_key=key, query=query))
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        auth_msg = format_mcp_auth_error(e)
        print(auth_msg or f"Agent error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Response: {reply}")
