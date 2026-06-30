from datetime import datetime, timedelta, timezone
from typing import Any

from database.connections import Database


def _parse_until(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


async def is_user_premium(db: Database, telegram_id: int) -> bool:
    user = await get_user(db, telegram_id)
    if not user or not user.get("is_premium"):
        return False

    until = _parse_until(user.get("premium_until"))
    if until and until < datetime.now(timezone.utc):
        await update_user(db, telegram_id, is_premium=0, premium_until=None)
        return False

    return True


async def activate_premium(
    db: Database, telegram_id: int, days: int
) -> datetime:
    user = await get_user(db, telegram_id)
    now = datetime.now(timezone.utc)
    base = now

    if user:
        current_until = _parse_until(user.get("premium_until"))
        if current_until and current_until > now:
            base = current_until

    until = base + timedelta(days=days)
    until_naive = until.astimezone(timezone.utc).replace(tzinfo=None)
    stored = until_naive.isoformat() if db.backend == "sqlite" else until_naive
    await update_user(db, telegram_id, is_premium=1, premium_until=stored)
    return until_naive


async def get_user(db: Database, telegram_id: int) -> dict[str, Any] | None:
    return await db.fetchone(
        "SELECT * FROM users WHERE telegram_id = ?", telegram_id
    )


async def create_user(
    db: Database,
    telegram_id: int,
    name: str,
    age: int,
    gender: str,
    target_gender: str,
    city: str,
    photo_id: str,
    bio: str,
) -> None:
    await db.execute(
        """
        INSERT INTO users (
            telegram_id, name, age, gender, target_gender, city, photo_id, bio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        telegram_id,
        name,
        age,
        gender,
        target_gender,
        city,
        photo_id,
        bio,
    )


async def update_user(db: Database, telegram_id: int, **fields: Any) -> None:
    if not fields:
        return
    columns = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [telegram_id]
    await db.execute(
        f"UPDATE users SET {columns} WHERE telegram_id = ?", *values
    )


async def set_user_active(db: Database, telegram_id: int, is_active: bool) -> None:
    await update_user(db, telegram_id, is_active=1 if is_active else 0)


async def get_next_profile(
    db: Database, viewer_id: int, target_gender: str
) -> dict[str, Any] | None:
    gender_filter = ""
    params: list[Any] = [viewer_id, viewer_id]
    if target_gender != "all":
        gender_filter = "AND u.gender = ?"
        params.insert(1, target_gender)

    return await db.fetchone(
        f"""
        SELECT u.*
        FROM users u
        WHERE u.telegram_id != ?
          AND u.is_active = 1
          {gender_filter}
          AND u.telegram_id NOT IN (
              SELECT to_user_id FROM actions WHERE from_user_id = ?
          )
        ORDER BY u.is_premium DESC, RANDOM()
        LIMIT 1
        """,
        *params,
    )


async def add_action(
    db: Database, from_user_id: int, to_user_id: int, action_type: str
) -> None:
    if db.backend == "sqlite":
        await db.execute(
            """
            INSERT OR REPLACE INTO actions (from_user_id, to_user_id, action_type)
            VALUES (?, ?, ?)
            """,
            from_user_id,
            to_user_id,
            action_type,
        )
        return

    await db.execute(
        """
        INSERT INTO actions (from_user_id, to_user_id, action_type)
        VALUES (?, ?, ?)
        ON CONFLICT (from_user_id, to_user_id)
        DO UPDATE SET action_type = EXCLUDED.action_type
        """,
        from_user_id,
        to_user_id,
        action_type,
    )


async def has_mutual_like(db: Database, user_a: int, user_b: int) -> bool:
    row = await db.fetchone(
        """
        SELECT 1 AS ok FROM actions
        WHERE from_user_id = ? AND to_user_id = ? AND action_type = 'like'
        """,
        user_b,
        user_a,
    )
    return row is not None


async def create_match(db: Database, user_one: int, user_two: int) -> bool:
    a, b = sorted([user_one, user_two])
    existing = await db.fetchone(
        "SELECT 1 AS ok FROM matches WHERE user_one = ? AND user_two = ?", a, b
    )
    if existing:
        return False
    await db.execute(
        "INSERT INTO matches (user_one, user_two) VALUES (?, ?)", a, b
    )
    return True


async def get_user_matches(db: Database, telegram_id: int) -> list[dict[str, Any]]:
    return await db.fetchall(
        """
        SELECT u.*
        FROM matches m
        JOIN users u ON (
            (m.user_one = ? AND u.telegram_id = m.user_two)
            OR (m.user_two = ? AND u.telegram_id = m.user_one)
        )
        ORDER BY m.created_at DESC
        """,
        telegram_id,
        telegram_id,
    )


async def are_matched(db: Database, user_a: int, user_b: int) -> bool:
    a, b = sorted([user_a, user_b])
    row = await db.fetchone(
        "SELECT 1 AS ok FROM matches WHERE user_one = ? AND user_two = ?", a, b
    )
    return row is not None


async def grant_item(db: Database, telegram_id: int, item_key: str) -> None:
    if db.backend == "sqlite":
        await db.execute(
            """
            INSERT OR REPLACE INTO user_items (telegram_id, item_key)
            VALUES (?, ?)
            """,
            telegram_id,
            item_key,
        )
        return
    await db.execute(
        """
        INSERT INTO user_items (telegram_id, item_key) VALUES (?, ?)
        ON CONFLICT (telegram_id, item_key) DO NOTHING
        """,
        telegram_id,
        item_key,
    )


async def has_item(db: Database, telegram_id: int, item_key: str) -> bool:
    row = await db.fetchone(
        "SELECT 1 AS ok FROM user_items WHERE telegram_id = ? AND item_key = ?",
        telegram_id,
        item_key,
    )
    return row is not None


async def get_user_items(db: Database, telegram_id: int) -> list[str]:
    rows = await db.fetchall(
        "SELECT item_key FROM user_items WHERE telegram_id = ? ORDER BY purchased_at DESC",
        telegram_id,
    )
    return [r["item_key"] for r in rows]
