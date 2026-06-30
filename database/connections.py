import re
from pathlib import Path
from typing import Any

import aiosqlite
import asyncpg

from config.settings import BASE_DIR, get_settings

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    target_gender TEXT NOT NULL,
    city TEXT NOT NULL,
    photo_id TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    is_premium INTEGER NOT NULL DEFAULT 0,
    premium_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,
    to_user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('like', 'dislike')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (from_user_id, to_user_id),
    FOREIGN KEY (from_user_id) REFERENCES users (telegram_id),
    FOREIGN KEY (to_user_id) REFERENCES users (telegram_id)
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_one INTEGER NOT NULL,
    user_two INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_one, user_two),
    FOREIGN KEY (user_one) REFERENCES users (telegram_id),
    FOREIGN KEY (user_two) REFERENCES users (telegram_id)
);

CREATE TABLE IF NOT EXISTS user_items (
    telegram_id INTEGER NOT NULL,
    item_key TEXT NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, item_key),
    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
);
"""

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(20) NOT NULL,
    target_gender VARCHAR(20) NOT NULL,
    city VARCHAR(255) NOT NULL,
    photo_id TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1,
    is_premium INTEGER NOT NULL DEFAULT 0,
    premium_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS actions (
    id SERIAL PRIMARY KEY,
    from_user_id BIGINT NOT NULL REFERENCES users (telegram_id),
    to_user_id BIGINT NOT NULL REFERENCES users (telegram_id),
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('like', 'dislike')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (from_user_id, to_user_id)
);

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    user_one BIGINT NOT NULL REFERENCES users (telegram_id),
    user_two BIGINT NOT NULL REFERENCES users (telegram_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_one, user_two)
);

CREATE TABLE IF NOT EXISTS user_items (
    telegram_id BIGINT NOT NULL REFERENCES users (telegram_id),
    item_key VARCHAR(50) NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, item_key)
);
"""


def _convert_placeholders(query: str) -> str:
    index = 0

    def repl(_: re.Match[str]) -> str:
        nonlocal index
        index += 1
        return f"${index}"

    return re.sub(r"\?", repl, query)


class Database:
    def __init__(self) -> None:
        settings = get_settings()
        self.url = settings.database_url
        self.backend = "sqlite" if self.url.startswith("sqlite:///") else "postgresql"
        self._sqlite: aiosqlite.Connection | None = None
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.backend == "sqlite":
            raw = self.url.replace("sqlite:///", "", 1)
            db_path = Path(raw) if Path(raw).is_absolute() else BASE_DIR / raw
            self._sqlite = await aiosqlite.connect(db_path)
            self._sqlite.row_factory = aiosqlite.Row
            await self._sqlite.executescript(SQLITE_SCHEMA)
            await self._sqlite.commit()
            await self._migrate_sqlite()
            return

        self._pool = await asyncpg.create_pool(self.url, min_size=1, max_size=5)
        async with self._pool.acquire() as conn:
            await conn.execute(PG_SCHEMA)
        await self._migrate_postgres()

    async def _migrate_sqlite(self) -> None:
        assert self._sqlite
        for sql in (
            "ALTER TABLE users ADD COLUMN is_premium INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN premium_until TIMESTAMP",
            """
            CREATE TABLE IF NOT EXISTS user_items (
                telegram_id INTEGER NOT NULL,
                item_key TEXT NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, item_key),
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
            )
            """,
        ):
            try:
                await self._sqlite.execute(sql)
                await self._sqlite.commit()
            except Exception:
                pass

    async def _migrate_postgres(self) -> None:
        assert self._pool
        async with self._pool.acquire() as conn:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_premium INTEGER NOT NULL DEFAULT 0"
            )
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS premium_until TIMESTAMP"
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_items (
                    telegram_id BIGINT NOT NULL REFERENCES users (telegram_id),
                    item_key VARCHAR(50) NOT NULL,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (telegram_id, item_key)
                )
                """
            )

    async def close(self) -> None:
        if self._sqlite:
            await self._sqlite.close()
            self._sqlite = None
        if self._pool:
            await self._pool.close()
            self._pool = None

    def _prepare(self, query: str) -> str:
        if self.backend == "sqlite":
            return query
        return _convert_placeholders(query)

    async def execute(self, query: str, *args: Any) -> None:
        query = self._prepare(query)
        if self._sqlite:
            await self._sqlite.execute(query, args)
            await self._sqlite.commit()
            return
        assert self._pool
        async with self._pool.acquire() as conn:
            await conn.execute(query, *args)

    async def fetchone(self, query: str, *args: Any) -> dict[str, Any] | None:
        query = self._prepare(query)
        if self._sqlite:
            cursor = await self._sqlite.execute(query, args)
            row = await cursor.fetchone()
            return dict(row) if row else None
        assert self._pool
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetchall(self, query: str, *args: Any) -> list[dict[str, Any]]:
        query = self._prepare(query)
        if self._sqlite:
            cursor = await self._sqlite.execute(query, args)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        assert self._pool
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
