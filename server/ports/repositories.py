from typing import Protocol

from server.domain.models import UserRecord


class UserRepository(Protocol):
    """Persistence port for resolving users by username (static or database)."""

    async def get_by_username(self, username: str) -> UserRecord | None:
        """Return the user if found; username match is case-insensitive."""
        ...
