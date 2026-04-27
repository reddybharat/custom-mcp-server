import server.env  # noqa: F401

import logging
import os
from functools import lru_cache
from typing import Final

from jwt import InvalidTokenError
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

from server.services.jwt_service import get_jwt_service
from server.services.rbac import scopes_for_role

LOGGER: Final = logging.getLogger(__name__)
DEFAULT_PUBLIC_BASE_URL: Final[str] = "http://localhost:8000"


class HS256TokenVerifier(TokenVerifier):
    """JWT verifier for FastMCP; scopes are derived from the signed role claim only."""

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            jwt_svc = get_jwt_service()
            payload = jwt_svc.decode_access_token(token)
            role = payload.get("role")
            if not role:
                return None
            scopes = scopes_for_role(str(role))
            username = str(payload.get("sub", ""))
            user_id = payload.get("id")
            client_id = str(user_id) if user_id is not None else username
            exp = payload.get("exp")
            expires_at_int = int(exp) if isinstance(exp, (int, float)) else None
            return AccessToken(
                token=token,
                client_id=client_id,
                scopes=scopes,
                expires_at=expires_at_int,
            )
        except InvalidTokenError as exc:
            LOGGER.info("JWT validation failed: %s", exc.__class__.__name__)
            return None
        except Exception:
            LOGGER.exception("Unexpected JWT verification failure")
            return None


@lru_cache
def get_token_verifier() -> HS256TokenVerifier:
    _ = get_jwt_service()
    return HS256TokenVerifier()


def create_auth_settings(mount_path: str, required_scopes: list[str] | None = None) -> AuthSettings:
    base_url = os.getenv("PUBLIC_BASE_URL", DEFAULT_PUBLIC_BASE_URL).rstrip("/")
    normalized_mount = mount_path.strip("/")
    resource_server_url = f"{base_url}/{normalized_mount}/mcp"
    issuer_url = os.getenv("JWT_ISSUER", base_url)
    scopes = required_scopes if required_scopes is not None else []
    return AuthSettings(
        issuer_url=issuer_url,
        resource_server_url=resource_server_url,
        required_scopes=scopes,
    )


def create_authenticated_mcp(
    name: str,
    mount_path: str,
    required_scopes: list[str] | None = None,
) -> FastMCP:
    scopes = required_scopes if required_scopes is not None else []
    return FastMCP(
        name,
        auth=create_auth_settings(mount_path, required_scopes=scopes),
        token_verifier=get_token_verifier(),
    )
