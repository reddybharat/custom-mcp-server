from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserRecord:
    """Application user for authentication (DB-agnostic)."""

    id: int
    username: str
    hashed_password: str
    role: str
