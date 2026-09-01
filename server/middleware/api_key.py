import logging
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

LOGGER = logging.getLogger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Guard MCP Starlette mounts with a shared ``MCP_API_KEY`` (``X-API-Key`` header)."""

    def __init__(self, app, *, guarded_prefixes: tuple[str, ...] = ()) -> None:
        super().__init__(app)
        self._guarded_prefixes = guarded_prefixes

    def _is_guarded(self, path: str) -> bool:
        return any(path == prefix or path.startswith(f"{prefix}/") for prefix in self._guarded_prefixes)

    async def dispatch(self, request: Request, call_next):
        if not self._is_guarded(request.url.path):
            return await call_next(request)

        expected = (os.getenv("MCP_API_KEY") or "").strip()
        if not expected:
            LOGGER.error("MCP_API_KEY is not configured; rejecting %s", request.url.path)
            return JSONResponse(
                status_code=503,
                content={"detail": "MCP API key not configured on server"},
            )

        provided = (request.headers.get("X-API-Key") or "").strip()
        if not provided or not secrets.compare_digest(provided, expected):
            LOGGER.warning("API key rejected for %s", request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
