from config import HOMEWORK_CATEGORIES

from .connection import db_execute

# =========================================================
# CATEGORIES - SEED
# =========================================================
# config.HOMEWORK_CATEGORIES is the source of truth for which
# categories exist and which channel they post to. Re-running this
# on every startup keeps the DB in sync if that dict ever changes
# (new code -> new row; existing code -> name/channel refreshed,
# password/is_active left untouched since those are admin-owned
# runtime state, not code).

async def seed_homework_categories():
    for code, info in HOMEWORK_CATEGORIES.items():
        await db_execute(
            """
            INSERT INTO homework_categories
            (code, name, channel_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                name=EXCLUDED.name,
                channel_id=EXCLUDED.channel_id,
                updated_at=NOW()
            """,
            (code, info["name"], info["channel_id"]),
        )


# =========================================================
# CATEGORIES - READ
# =========================================================

async def get_homework_categories():
    return await db_execute(
        """
        SELECT *
        FROM homework_categories
        ORDER BY id
        """,
        fetchall=True,
    )


async def get_active_homework_categories():
    return await db_execute(
        """
        SELECT *
        FROM homework_categories
        WHERE is_active=TRUE
        ORDER BY id
        """,
        fetchall=True,
    )


async def get_homework_category(category_id: int):
    return await db_execute(
        """
        SELECT *
        FROM homework_categories
        WHERE id=%s
        """,
        (category_id,),
        fetchone=True,
    )


async def get_homework_category_by_code(code: str):
    return await db_execute(
        """
        SELECT *
        FROM homework_categories
        WHERE code=%s
        """,
        (code,),
        fetchone=True,
    )


# =========================================================
# CATEGORIES - ADMIN MANAGEMENT
# =========================================================

async def set_homework_category_password(
    category_id: int,
    password_hash: str,
    password_salt: str,
):
    await db_execute(
        """
        UPDATE homework_categories
        SET
            password_hash=%s,
            password_salt=%s,
            updated_at=NOW()
        WHERE id=%s
        """,
        (password_hash, password_salt, category_id),
    )


async def set_homework_category_active(category_id: int, is_active: bool):
    await db_execute(
        """
        UPDATE homework_categories
        SET
            is_active=%s,
            updated_at=NOW()
        WHERE id=%s
        """,
        (is_active, category_id),
    )


# =========================================================
# MEMBERSHIPS - READ
# =========================================================

async def get_membership(user_id: int, category_id: int):
    return await db_execute(
        """
        SELECT *
        FROM homework_memberships
        WHERE user_id=%s
        AND category_id=%s
        """,
        (user_id, category_id),
        fetchone=True,
    )


async def get_user_memberships(user_id: int):
    return await db_execute(
        """
        SELECT
            m.*,
            c.code,
            c.name AS category_name
        FROM homework_memberships m
        INNER JOIN homework_categories c ON c.id = m.category_id
        WHERE m.user_id=%s
        ORDER BY m.created_at
        """,
        (user_id,),
        fetchall=True,
    )


# =========================================================
# MEMBERSHIPS - WRITE
# =========================================================

async def create_membership(
    user_id: int,
    category_id: int,
    first_name: str,
    last_name: str,
    level: str,
    lesson_number: int,
):
    await db_execute(
        """
        INSERT INTO homework_memberships
        (user_id, category_id, first_name, last_name, level, lesson_number)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, category_id) DO UPDATE SET
            first_name=EXCLUDED.first_name,
            last_name=EXCLUDED.last_name,
            level=EXCLUDED.level,
            lesson_number=EXCLUDED.lesson_number,
            updated_at=NOW()
        """,
        (
            user_id,
            category_id,
            first_name,
            last_name,
            level,
            lesson_number,
        ),
    )


async def update_membership_profile(
    user_id: int,
    category_id: int,
    first_name: str,
    last_name: str,
    level: str,
    lesson_number: int,
):
    """
    Editing a profile only changes the membership row - past
    submissions keep the snapshot they were created with (see
    homework_submissions.first_name/last_name/level/lesson_number).
    """

    await db_execute(
        """
        UPDATE homework_memberships
        SET
            first_name=%s,
            last_name=%s,
            level=%s,
            lesson_number=%s,
            updated_at=NOW()
        WHERE user_id=%s
        AND category_id=%s
        """,
        (
            first_name,
            last_name,
            level,
            lesson_number,
            user_id,
            category_id,
        ),
    )


# =========================================================
# ADMIN - STATISTICS / BROWSING
# =========================================================

async def get_category_member_count(category_id: int) -> int:
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_memberships
        WHERE category_id=%s
        """,
        (category_id,),
        fetchone=True,
    )

    return row["count"]


async def get_homework_users(category_id: int | None = None, limit: int = 30, offset: int = 0):
    """
    Members joined with their submission count + total score, for
    the Admin Panel's "Foydalanuvchilar" browser. Optionally scoped
    to one category.
    """

    return await db_execute(
        """
        SELECT
            m.user_id,
            m.first_name,
            m.last_name,
            m.level,
            m.lesson_number,
            c.id AS category_id,
            c.code,
            c.name AS category_name,
            COUNT(s.id) AS submission_count,
            COALESCE(SUM(e.score), 0) AS total_score
        FROM homework_memberships m
        INNER JOIN homework_categories c ON c.id = m.category_id
        LEFT JOIN homework_submissions s
            ON s.user_id = m.user_id AND s.category_id = m.category_id
        LEFT JOIN homework_evaluations e ON e.submission_id = s.id
        WHERE (%(category_id)s IS NULL OR m.category_id = %(category_id)s)
        GROUP BY m.user_id, m.first_name, m.last_name, m.level,
                 m.lesson_number, c.id, c.code, c.name
        ORDER BY m.created_at DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {"category_id": category_id, "limit": limit, "offset": offset},
        fetchall=True,
    )


async def count_homework_users(category_id: int | None = None) -> int:
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_memberships
        WHERE (%(category_id)s IS NULL OR category_id = %(category_id)s)
        """,
        {"category_id": category_id},
        fetchone=True,
    )

    return row["count"]
