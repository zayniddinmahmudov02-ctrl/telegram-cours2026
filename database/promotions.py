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
# DROP LEGACY PER-COURSE ROWS
# =========================================================
# Early version of this table kept one deadline per course, seeded
# the first time each course's info screen was opened - so A1-B1 and
# A1-C1 could (and did) end up with two different deadlines, neither
# starting at deploy time. Those rows are no longer read by anything;
# this removes them so no stale deadline lingers in the table.
# Idempotent - a no-op on every run after the first.

_LEGACY_COURSE_KEYS = (
    "🔥 A1-B1",
    "🔥 A1-C1",
)


async def drop_legacy_course_promotion_rows():
    await db_execute(
        """
        DELETE FROM promotions
        WHERE course = ANY(%s);
        """,
        (list(_LEGACY_COURSE_KEYS),),
    )


# =========================================================
# GET OR CREATE GLOBAL DEADLINE
# =========================================================
# One deadline, shared by every promoted course and every user - set
# exactly once (the first caller wins via ON CONFLICT DO NOTHING) so
# every user, every course listed in config.COURSE_PROMOTIONS, and
# every future bot/server restart keeps seeing the same countdown
# target.

_GLOBAL_PROMOTION_KEY = "GLOBAL_PROMOTION_DEADLINE"


async def get_or_create_global_promotion_deadline(promo_days: int):
    deadline = datetime.now(timezone.utc) + timedelta(days=promo_days)

    row = await db_execute(
        """
        INSERT INTO promotions (course, deadline)
        VALUES (%s, %s)
        ON CONFLICT (course) DO NOTHING
        RETURNING deadline;
        """,
        (_GLOBAL_PROMOTION_KEY, deadline),
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
        (_GLOBAL_PROMOTION_KEY,),
        fetchone=True,
    )

    return row["deadline"]
