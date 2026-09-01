from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import os

"""
MCP client URLs and auth headers.

Pass the API key into ``build_server_config(api_key=...)`` or set ``MCP_API_KEY``.

Set MCP_SERVER_URL (e.g. http://127.0.0.1:8000) so client URLs match the API.
"""

MCP_MOUNTS = {"Math": "/math/mcp", "Weather": "/weather/mcp"}


def mcp_server_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


def build_server_config(*, api_key: str | None = None) -> dict:
    """Build MultiServerMCPClient config with ``X-API-Key`` when ``api_key`` is set."""
    headers: dict[str, str] = {}
    if api_key and api_key.strip():
        headers["X-API-Key"] = api_key.strip()
    base = mcp_server_url()
    return {
        "Math": {
            "url": f"{base}{MCP_MOUNTS['Math']}",
            "transport": "streamable_http",
            "headers": headers,
        },
        "Weather": {
            "url": f"{base}{MCP_MOUNTS['Weather']}",
            "transport": "streamable_http",
            "headers": headers,
        },
    }
