from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import os

"""
MCP client URLs and auth headers.

Pass the JWT from ``POST /auth/token`` into ``build_server_config(bearer_token=...)``.

Set MCP_SERVER_URL (e.g. http://127.0.0.1:8000) so client URLs match the API.

Alternatively set MCP_BEARER_TOKEN in the environment (used when no interactive login).
"""


def mcp_server_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")


def build_server_config(*, bearer_token: str | None = None) -> dict:
    """Build MultiServerMCPClient config. Use bearer_token from ``POST /auth/token``."""
    headers: dict[str, str] = {}
    if bearer_token and bearer_token.strip():
        headers["Authorization"] = f"Bearer {bearer_token.strip()}"
    base = mcp_server_url()
    return {
        "Math": {
            "url": f"{base}/math/mcp",
            "transport": "streamable_http",
            "headers": headers,
        },
        "Weather": {
            "url": f"{base}/weather/mcp",
            "transport": "streamable_http",
            "headers": headers,
        },
    }
