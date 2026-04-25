import server.env  # noqa: F401

import os
from functools import lru_cache

from server.adapters.persistence.db_user_repository import DatabaseUserRepository
from server.adapters.persistence.static_user_repository import StaticUserRepository
from server.ports.repositories import UserRepository


@lru_cache
def get_user_repository() -> UserRepository:
    mode = os.getenv("USER_STORE", "static").strip().lower()
    if mode == "database":
        return DatabaseUserRepository()
    return StaticUserRepository()
