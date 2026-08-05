from .connection import db_execute


# =========================================================
# FAVORITE MUSIC
# =========================================================
# Personal per-user favorites for the Musik gallery. Each row is
# keyed by (telegram_id, message_id) so a user can only favorite
# a given song once.

async def is_favorite_music(telegram_id: int, message_id: int) -> bool:
    row = await db_execute(
        """
        SELECT id

        FROM favorite_music

        WHERE
            telegram_id=%s

        AND
            message_id=%s
        """,
        (telegram_id, message_id),
        fetchone=True,
    )

    return row is not None


async def add_favorite_music(telegram_id: int, message_id: int):
    await db_execute(
        """
        INSERT INTO favorite_music (telegram_id, message_id)
        VALUES (%s, %s)
        ON CONFLICT (telegram_id, message_id) DO NOTHING
        """,
        (telegram_id, message_id),
    )


async def remove_favorite_music(telegram_id: int, message_id: int):
    await db_execute(
        """
        DELETE FROM favorite_music

        WHERE
            telegram_id=%s

        AND
            message_id=%s
        """,
        (telegram_id, message_id),
    )


async def toggle_favorite_music(telegram_id: int, message_id: int) -> bool:
    """Adds/removes the favorite and returns the new state (True = now favorite)."""

    if await is_favorite_music(telegram_id, message_id):
        await remove_favorite_music(telegram_id, message_id)
        return False

    await add_favorite_music(telegram_id, message_id)
    return True


async def get_favorite_music_ids(telegram_id: int) -> list[int]:
    rows = await db_execute(
        """
        SELECT message_id

        FROM favorite_music

        WHERE telegram_id=%s

        ORDER BY created_at DESC
        """,
        (telegram_id,),
        fetchall=True,
    )

    return [row["message_id"] for row in rows]
