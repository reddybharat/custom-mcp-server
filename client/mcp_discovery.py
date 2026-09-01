"""MCP server discovery for the Streamlit Connection tab."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_mcp_adapters.client import MultiServerMCPClient

from client.config import server_name_from_mcp_url


@dataclass(frozen=True)
class ToolInfo:
    name: str
    description: str


@dataclass(frozen=True)
class PromptInfo:
    name: str
    description: str


@dataclass(frozen=True)
class ServerDiscovery:
    name: str
    url: str
    tools: list[ToolInfo]
    resources: list[str]
    prompts: list[PromptInfo]


async def discover_server(
    client: MultiServerMCPClient,
    *,
    mcp_url: str,
    server_name: str | None = None,
) -> ServerDiscovery:
    """List tools, resources, and prompts for one MCP endpoint."""
    name = server_name or server_name_from_mcp_url(mcp_url)
    url = mcp_url.rstrip("/")

    tools_raw = await client.get_tools(server_name=name)
    tools = [
        ToolInfo(name=t.name, description=(t.description or "").strip())
        for t in tools_raw
    ]

    async with client.session(name) as session:
        lp = await session.list_prompts()
        lr = await session.list_resources()

    prompts = [
        PromptInfo(
            name=p.name,
            description=(getattr(p, "description", None) or "").strip(),
        )
        for p in lp.prompts
    ]
    resources = sorted({str(r.uri) for r in lr.resources})

    return ServerDiscovery(
        name=name,
        url=url,
        tools=tools,
        resources=resources,
        prompts=prompts,
    )
