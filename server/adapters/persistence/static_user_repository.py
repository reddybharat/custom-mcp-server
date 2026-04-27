import os
import re

import bcrypt

from server.domain.models import UserRecord

_BCRYPT_PREFIX = re.compile(r"^\$2[aby]\$\d{2}\$.+")


def _hashed_password_from_env() -> str:
    raw_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if raw_hash is not None and (h := raw_hash.strip()):
        if not _BCRYPT_PREFIX.match(h):
            raise RuntimeError(
                "ADMIN_PASSWORD_HASH must look like a bcrypt hash (e.g. starting with $2b$)."
            )
        return h
    plain = os.getenv("ADMIN_PASSWORD")
    if plain in (None, ""):
        plain = "admin"
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


class StaticUserRepository:
    """Single user: ADMIN_USERNAME + ADMIN_PASSWORD_HASH, or ADMIN_PASSWORD (hashed at startup)."""

    def __init__(self) -> None:
        username = (os.getenv("ADMIN_USERNAME") or "admin").strip() or "admin"
        hashed = _hashed_password_from_env()
        key = username.lower()
        self._by_username = {
            key: UserRecord(
                id=1,
                username=username,
                hashed_password=hashed,
                role="admin",
            ),
        }

    async def get_by_username(self, username: str) -> UserRecord | None:
        return self._by_username.get(username.strip().lower())
