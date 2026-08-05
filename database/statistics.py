import asyncio

from .connection import db_execute


# =========================================================
# USERS
# =========================================================

async def users_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        """,
        fetchone=True,
    )
    return row["count"]


async def approved_users_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE approved=TRUE
        """,
        fetchone=True,
    )
    return row["count"]


async def pending_users_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE approved=FALSE
        """,
        fetchone=True,
    )
    return row["count"]


# =========================================================
# PAYMENTS
# =========================================================

async def buyers_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM payments
        WHERE status='approved'
        """,
        fetchone=True,
    )
    return row["count"]


async def pending_payments_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM payments
        WHERE status='pending'
        """,
        fetchone=True,
    )
    return row["count"]


async def total_income():
    row = await db_execute(
        """
        SELECT COALESCE(SUM(amount),0) AS total
        FROM payments
        WHERE status='approved'
        """,
        fetchone=True,
    )
    return row["total"]


# =========================================================
# CERTIFICATES
# =========================================================

async def certificates_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM certificates
        """,
        fetchone=True,
    )
    return row["count"]


# =========================================================
# MEDIA
# =========================================================

async def films_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM films
        """,
        fetchone=True,
    )
    return row["count"]


async def books_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM books
        """,
        fetchone=True,
    )
    return row["count"]


async def music_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM music
        """,
        fetchone=True,
    )
    return row["count"]


async def videos_count():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM videos
        """,
        fetchone=True,
    )
    return row["count"]


# =========================================================
# RANKING
# =========================================================

async def top_total_users(limit=100):
    return await db_execute(
        """
        SELECT
            full_name,
            total_score
        FROM users
        WHERE approved=TRUE
        ORDER BY total_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


async def top_daily_users(limit=100):
    return await db_execute(
        """
        SELECT
            full_name,
            daily_score
        FROM users
        WHERE approved=TRUE
        ORDER BY daily_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


# =========================================================
# REGISTRATION
# =========================================================

async def today_registered():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE DATE(created_at)=CURRENT_DATE
        """,
        fetchone=True,
    )
    return row["count"]


async def this_month_registered():
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE DATE_TRUNC('month', created_at)=DATE_TRUNC('month', CURRENT_DATE)
        """,
        fetchone=True,
    )
    return row["count"]


# =========================================================
# DASHBOARD
# =========================================================

async def get_dashboard():
    # 12 independent COUNT/SUM queries - fetched concurrently
    # instead of 12 sequential round trips.
    (
        users,
        approved,
        pending_users_,
        buyers,
        pending_payments_,
        income,
        certificates,
        films,
        books,
        music,
        videos,
        today,
        month,
    ) = await asyncio.gather(
        users_count(),
        approved_users_count(),
        pending_users_count(),
        buyers_count(),
        pending_payments_count(),
        total_income(),
        certificates_count(),
        films_count(),
        books_count(),
        music_count(),
        videos_count(),
        today_registered(),
        this_month_registered(),
    )

    return {
        "users": users,
        "approved": approved,
        "pending_users": pending_users_,

        "buyers": buyers,
        "pending_payments": pending_payments_,
        "income": income,

        "certificates": certificates,

        "films": films,
        "books": books,
        "music": music,
        "videos": videos,

        "today": today,
        "month": month,
    }
