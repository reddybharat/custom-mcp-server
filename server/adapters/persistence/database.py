"""
Database session boilerplate (SQLAlchemy 2.x async) — **not wired by default**.

When you implement ``USER_STORE=database``:

1. **Uncomment** optional dependencies in ``requirements.txt`` (``sqlalchemy[asyncio]``, driver e.g. ``asyncpg``).

2. Set ``DATABASE_URL`` to an async URL, for example::
       postgresql+asyncpg://user:pass@localhost:5432/mydb

3. Instantiate an engine once at process startup (or use FastAPI ``lifespan``)::

       # from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
       #
       # engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
       # SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

4. **Dependency injection:** expose ``async def get_session()`` yielding ``AsyncSession``,
   or store ``SessionLocal`` on ``app.state`` and pass the factory into ``DatabaseUserRepository``.

5. **Alembic:** run ``alembic init alembic``, point ``sqlalchemy.url`` at the same DB,
   autogenerate revisions against your ORM models, and run ``alembic upgrade head`` in CI/deploy.

6. **Pooling:** for production, tune ``pool_size``, ``max_overflow``, and optionally
   ``pool_pre_ping=True`` on ``create_async_engine``.

7. **Secrets:** never commit ``DATABASE_URL``; use env or a secret manager.

This module intentionally contains **no** live imports so static-user mode works without drivers.
"""

# Example (uncomment when ready):
#
# import os
# from collections.abc import AsyncIterator
# from contextlib import asynccontextmanager
#
# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
#
# _engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
# _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
#
#
# @asynccontextmanager
# async def session_scope() -> AsyncIterator[AsyncSession]:
#     async with _session_factory() as session:
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
