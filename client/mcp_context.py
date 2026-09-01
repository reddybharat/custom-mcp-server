"""MCP prompts/resources via MultiServerMCPClient: bootstrap and selective context."""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.documents.base import Blob
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

LOGGER = logging.getLogger(__name__)

MATH_SERVER = "Math"
WEATHER_SERVER = "Weather"
MATH_RESOURCE_URI = "resource://math/capabilities"
WEATHER_RESOURCE_URI = "resource://weather/capabilities"
MATH_PROMPT_NAME = "math_assistant"
WEATHER_PROMPT_NAME = "weather_assistant"

_WEATHER_KEYS = frozenset(
    (
        "weather",
        "temperature",
        "rain",
        "forecast",
        "humidity",
        "celsius",
        "fahrenheit",
        "wind",
        "snow",
        "storm",
    )
)
_MATH_KEYS = frozenset(
    (
        "calculate",
        "sum ",
        "plus ",
        " minus ",
        " times ",
        "divide",
        "multiply",
        "multiplication",
        "subtrac",
        "addition",
        "product ",
        "quotient",
        "math",
    )
)


def _prompt_messages_to_text(messages: list[HumanMessage | AIMessage]) -> str:
    parts: list[str] = []
    for m in messages:
        c = m.content
        if isinstance(c, str):
            parts.append(c.strip())
        else:
            parts.append(str(c).strip())
    return "\n".join(p for p in parts if p)


def _blobs_to_text(blobs: list[Blob]) -> str:
    parts: list[str] = []
    for b in blobs:
        try:
            s = b.as_string().strip()
            if s:
                parts.append(s)
        except Exception:
            LOGGER.debug("Skipping blob that could not be read as text", exc_info=True)
    return "\n\n".join(parts)


async def _silent(coro: Any) -> Any:
    try:
        return await coro
    except Exception as exc:
        LOGGER.debug("MCP fetch skipped: %s", exc)
        return None


async def _mcp_listing_lines(client: MultiServerMCPClient, server: str) -> str:
    async with client.session(server) as session:
        lp = await session.list_prompts()
        lr = await session.list_resources()
        pnames = ", ".join(sorted({p.name for p in lp.prompts}))
        ruris = ", ".join(sorted({str(r.uri) for r in lr.resources}))
        lines = [f"[{server}] Listed MCP prompts: {pnames or '(none)'}"]
        lines.append(f"[{server}] Listed MCP resources: {ruris or '(none)'}")
        return "\n".join(lines)


async def mcp_bootstrap_system_extension(client: MultiServerMCPClient) -> str:
    """Prompts, explicit capability resources, and optional list_* discovery for system prompt."""
    sections: list[str] = []

    math_msgs = await _silent(
        client.get_prompt(MATH_SERVER, MATH_PROMPT_NAME, arguments={"focus": "general"})
    )
    if isinstance(math_msgs, list) and math_msgs:
        sections.append("### Math MCP (prompt)\n" + _prompt_messages_to_text(math_msgs))

    wx_msgs = await _silent(
        client.get_prompt(WEATHER_SERVER, WEATHER_PROMPT_NAME, arguments={})
    )
    if isinstance(wx_msgs, list) and wx_msgs:
        sections.append("### Weather MCP (prompt)\n" + _prompt_messages_to_text(wx_msgs))

    math_blobs = await _silent(client.get_resources(MATH_SERVER, uris=MATH_RESOURCE_URI))
    if isinstance(math_blobs, list) and math_blobs:
        sections.append("### Math MCP (resource)\n" + _blobs_to_text(math_blobs))

    wx_blobs = await _silent(client.get_resources(WEATHER_SERVER, uris=WEATHER_RESOURCE_URI))
    if isinstance(wx_blobs, list) and wx_blobs:
        sections.append("### Weather MCP (resource)\n" + _blobs_to_text(wx_blobs))

    for server in (MATH_SERVER, WEATHER_SERVER):
        disc = await _silent(_mcp_listing_lines(client, server))
        if isinstance(disc, str) and disc.strip():
            sections.append("### Discovery\n" + disc)

    return "\n\n".join(sections).strip()


_CITY_IN = re.compile(
    r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z]*(?:\s+[A-Za-z][A-Za-z]*)?)\b",
    re.IGNORECASE,
)


def _guess_city(user_text: str) -> str | None:
    m = _CITY_IN.search(user_text.strip())
    if not m:
        return None
    city = m.group(1).strip()
    if len(city) < 2:
        return None
    if city.lower() in {"the", "my", "this", "that", "a"}:
        return None
    return city


def _text_suggests_weather(user_text: str) -> bool:
    low = user_text.lower()
    if any(k in low for k in _WEATHER_KEYS):
        return True
    if "°" in user_text:
        return True
    return bool(_CITY_IN.search(user_text) and ("weather" in low or "temperature" in low))


def _text_suggests_math(user_text: str) -> bool:
    low = user_text.lower()
    if any(k in low for k in _MATH_KEYS):
        return True
    if re.search(r"\d\s*[\+\-\*\/]\s*\d", user_text):
        return True
    return False


async def selective_mcp_context(
    client: MultiServerMCPClient,
    user_text: str,
    *,
    max_chars: int = 2000,
) -> str:
    """Turn-specific get_prompt calls (richer arguments) when the message looks math/weather-related."""
    chunks: list[str] = []
    if _text_suggests_weather(user_text):
        args: dict[str, Any] = {}
        city = _guess_city(user_text)
        if city:
            args["city"] = city
        msgs = await _silent(
            client.get_prompt(WEATHER_SERVER, WEATHER_PROMPT_NAME, arguments=args or None)
        )
        if isinstance(msgs, list) and msgs:
            chunks.append(
                "### Weather MCP (turn-specific prompt)\n" + _prompt_messages_to_text(msgs)
            )

    if _text_suggests_math(user_text):
        focus = user_text.strip()
        if len(focus) > 200:
            focus = focus[:200] + "…"
        msgs = await _silent(
            client.get_prompt(MATH_SERVER, MATH_PROMPT_NAME, arguments={"focus": focus})
        )
        if isinstance(msgs, list) and msgs:
            chunks.append(
                "### Math MCP (turn-specific prompt)\n" + _prompt_messages_to_text(msgs)
            )

    out = "\n\n".join(chunks).strip()
    if len(out) > max_chars:
        return out[: max_chars - 1] + "…"
    return out
