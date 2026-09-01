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
DEFAULT_SERVER_NAME = "MCP"


def mcp_server_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


def _auth_headers(*, api_key: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if api_key and api_key.strip():
        headers["X-API-Key"] = api_key.strip()
    return headers


def server_name_from_mcp_url(mcp_url: str) -> str:
    """Infer a stable connection name from the MCP URL path."""
    path = mcp_url.rstrip("/").lower()
    if "/math" in path:
        return "Math"
    if "/weather" in path:
        return "Weather"
    return DEFAULT_SERVER_NAME


def build_single_server_config(
    *,
    mcp_url: str,
    api_key: str | None = None,
    server_name: str | None = None,
) -> dict:
    """Build MultiServerMCPClient config for one MCP endpoint."""
    name = server_name or server_name_from_mcp_url(mcp_url)
    return {
        name: {
            "url": mcp_url.rstrip("/"),
            "transport": "streamable_http",
            "headers": _auth_headers(api_key=api_key),
        }
    }


def build_server_config(*, api_key: str | None = None, base_url: str | None = None) -> dict:
    """Build MultiServerMCPClient config for all known mounts (CLI default)."""
    headers = _auth_headers(api_key=api_key)
    base = (base_url or mcp_server_url()).rstrip("/")
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
