from datetime import datetime, timedelta, timezone

from .connection import db_execute

# =========================================================
# CREATE TABLE
# =========================================================

async def create_promotions_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS promotions(

            course TEXT PRIMARY KEY,

            deadline TIMESTAMPTZ NOT NULL

        );
        """
    )


# =========================================================
# GET OR CREATE DEADLINE
# =========================================================
# The deadline for a course is set exactly once - the first caller
# wins via ON CONFLICT DO NOTHING - so every user and every future
# bot/server restart keeps seeing the same countdown target.

async def get_or_create_promotion_deadline(course: str, promo_days: int):
    deadline = datetime.now(timezone.utc) + timedelta(days=promo_days)

    row = await db_execute(
        """
        INSERT INTO promotions (course, deadline)
        VALUES (%s, %s)
        ON CONFLICT (course) DO NOTHING
        RETURNING deadline;
        """,
        (course, deadline),
        fetchone=True,
    )

    if row:
        return row["deadline"]

    row = await db_execute(
        """
        SELECT deadline
        FROM promotions
        WHERE course=%s;
        """,
        (course,),
        fetchone=True,
    )

    return row["deadline"]
