"""
Async DB-backed users — stub until you wire SQLAlchemy and a ``users`` table.

Integration steps (see also ``server.adapters.persistence.database``):

1. Define an ORM model, e.g. ``User`` with columns ``id``, ``username``, ``hashed_password``, ``role``.

2. Inject ``AsyncSession`` (or a callable returning one) into ``DatabaseUserRepository.__init__``.

3. Implement ``get_by_username``::

       # from sqlalchemy import select
       # from yourapp.models import User as UserORM
       #
       # async def get_by_username(self, username: str) -> UserRecord | None:
       #     async with self._session_factory() as session:
       #         stmt = select(UserORM).where(
       #             func.lower(UserORM.username) == username.strip().lower()
       #         )
       #         row = (await session.execute(stmt)).scalar_one_or_none()
       #         if row is None:
       #             return None
       #         return UserRecord(
       #             id=row.id,
       #             username=row.username,
       #             hashed_password=row.hashed_password,
       #             role=row.role,
       #         )

4. Set ``USER_STORE=database`` in ``.env`` and ensure ``server.deps.get_user_repository`` returns this class.

5. Seed users with bcrypt hashes (same format as ``ADMIN_PASSWORD_HASH`` for static mode).
"""

from server.domain.models import UserRecord


class DatabaseUserRepository:
    """Placeholder; replace ``NotImplementedError`` with ORM queries when DATABASE_URL is live."""

    async def get_by_username(self, username: str) -> UserRecord | None:
        raise NotImplementedError(
            "DatabaseUserRepository is a stub; implement with your ORM and users table."
        )
