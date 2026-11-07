import asyncio
import logging
import os

from ddgs import DDGS
from tavily import AsyncTavilyClient

import server.env  # noqa: F401 — ensure `.env` loaded for TAVILY_API_KEY

from mcp.server.fastmcp import FastMCP

LOGGER = logging.getLogger(__name__)

MAX_RESULTS = 5
TAVILY_TIMEOUT_S = 15
NO_RESULTS = "No web results."

search_mcp = FastMCP("Search")


@search_mcp.tool()
async def web_search(query: str) -> str:
    """
    Search the public web. Returns numbered results, each with a title, URL and snippet.
    """
    results: list[tuple[str, str, str]] = []
    source = "Tavily"
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key:
        try:
            response = await AsyncTavilyClient(api_key).search(
                query, max_results=MAX_RESULTS, topic="general", timeout=TAVILY_TIMEOUT_S
            )
            results = [(r["title"], r["url"], r["content"]) for r in response.get("results", [])]
        except Exception as e:
            LOGGER.warning("Tavily search failed (%s); falling back to DuckDuckGo", type(e).__name__)
    if not results:
        # ddgs is sync; it raises DDGSException when nothing is found, which FastMCP returns as isError.
        hits = await asyncio.to_thread(DDGS().text, query, max_results=MAX_RESULTS)
        results = [(h["title"], h["href"], h["body"]) for h in hits]
        source = "DuckDuckGo"
    if not results:
        return NO_RESULTS
    lines = [f"{i}. {title}\n{url}\n{snippet}" for i, (title, url, snippet) in enumerate(results, 1)]
    return "\n\n".join(lines) + f"\n\n(via {source})"
