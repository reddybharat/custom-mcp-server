from __future__ import annotations

import server.env  # noqa: F401

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from jwt import InvalidTokenError


@dataclass(frozen=True, slots=True)
class JwtService:
    secret: str
    algorithm: str
    issuer: str | None
    audience: str | None

    @classmethod
    def from_env(cls) -> JwtService:
        def _strip(s: str | None) -> str | None:
            if s is None:
                return None
            t = s.strip()
            if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"'):
                t = t[1:-1]
            return t.strip() or None

        secret = _strip(os.environ.get("JWT_SECRET"))
        if not secret:
            raise RuntimeError("JWT_SECRET environment variable is required.")
        algorithm = (os.environ.get("ALGORITHM") or "HS256").strip()
        issuer = _strip(os.environ.get("JWT_ISSUER"))
        audience = _strip(os.environ.get("JWT_AUDIENCE"))
        return cls(secret=secret, algorithm=algorithm, issuer=issuer, audience=audience)

    def encode_access_token(
        self,
        username: str,
        user_id: int,
        role: str,
        expires_delta: timedelta,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload: dict = {
            "sub": username,
            "id": user_id,
            "role": role,
            "exp": now + expires_delta,
            "iat": now,
        }
        if self.issuer:
            payload["iss"] = self.issuer
        if self.audience:
            payload["aud"] = self.audience
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> dict:
        options = {"require": ["exp", "sub", "id", "role"]}
        kwargs: dict = {
            "jwt": token,
            "key": self.secret,
            "algorithms": [self.algorithm],
            "options": options,
        }
        if self.issuer:
            kwargs["issuer"] = self.issuer
        if self.audience:
            kwargs["audience"] = self.audience
        return jwt.decode(**kwargs)


@lru_cache
def get_jwt_service() -> JwtService:
    return JwtService.from_env()


def decode_token_or_raise(token: str) -> dict:
    """Decode JWT; raise InvalidTokenError on failure."""
    return get_jwt_service().decode_access_token(token)
