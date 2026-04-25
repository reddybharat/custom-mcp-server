"""Role to MCP scope mapping (authorization). Scopes must match ``required_scopes`` on each FastMCP mount."""

from functools import lru_cache

_SCOPE_MATH = "mcp:math"
_SCOPE_WEATHER = "mcp:weather"


@lru_cache
def role_to_scopes(role: str) -> tuple[str, ...]:
    """
    Return MCP scopes for a role. Add new scope constants and map roles here when you add tools.
    """
    r = (role or "").strip().lower()
    if r in ("root", "admin"):
        return (_SCOPE_MATH, _SCOPE_WEATHER)
    if r == "analyst":
        return (_SCOPE_MATH,)
    if r == "viewer":
        return tuple()
    return tuple()


def scopes_for_role(role: str) -> list[str]:
    return list(role_to_scopes(role))
