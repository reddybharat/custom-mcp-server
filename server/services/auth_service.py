from __future__ import annotations

import server.env  # noqa: F401

import os
from dataclasses import dataclass
from datetime import timedelta

import bcrypt

from server.domain.models import UserRecord
from server.ports.repositories import UserRepository
from server.services.jwt_service import JwtService
from server.services.rbac import scopes_for_role


def _access_token_expires_delta() -> timedelta:
    return timedelta(minutes=float(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))


@dataclass(slots=True)
class AuthService:
    jwt_service: JwtService

    async def authenticate_async(
        self, repo: UserRepository, username: str, password: str
    ) -> UserRecord | None:
        user = await repo.get_by_username(username)
        if not user:
            return None
        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user.hashed_password.encode("ascii"),
        ):
            return None
        return user

    def issue_access_token(self, user: UserRecord) -> str:
        delta = _access_token_expires_delta()
        return self.jwt_service.encode_access_token(
            username=user.username,
            user_id=user.id,
            role=user.role,
            expires_delta=delta,
        )

    def issue_access_token_with_claims(self, user: UserRecord) -> tuple[str, list[str]]:
        scopes = scopes_for_role(user.role)
        return self.issue_access_token(user), scopes
