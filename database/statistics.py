from .connection import db_execute


# =========================================================
# USERS
# =========================================================

def users_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        """,
        fetchone=True,
    )
    return row[0]


def approved_users_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE approved=TRUE
        """,
        fetchone=True,
    )
    return row[0]


def pending_users_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE approved=FALSE
        """,
        fetchone=True,
    )
    return row[0]


# =========================================================
# PAYMENTS
# =========================================================

def buyers_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM payments
        WHERE status='approved'
        """,
        fetchone=True,
    )
    return row[0]


def pending_payments_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM payments
        WHERE status='pending'
        """,
        fetchone=True,
    )
    return row[0]


def total_income():
    row = db_execute(
        """
        SELECT COALESCE(SUM(amount),0)
        FROM payments
        WHERE status='approved'
        """,
        fetchone=True,
    )
    return row[0]


# =========================================================
# HOMEWORK
# =========================================================

def homework_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM homework
        """,
        fetchone=True,
    )
    return row[0]


def pending_homework_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM homework
        WHERE status='pending'
        """,
        fetchone=True,
    )
    return row[0]


# =========================================================
# CERTIFICATES
# =========================================================

def certificates_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM certificates
        """,
        fetchone=True,
    )
    return row[0]


# =========================================================
# MEDIA
# =========================================================

def films_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM films
        """,
        fetchone=True,
    )
    return row[0]


def books_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM books
        """,
        fetchone=True,
    )
    return row[0]


def music_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM music
        """,
        fetchone=True,
    )
    return row[0]


def videos_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM videos
        """,
        fetchone=True,
    )
    return row[0]


# =========================================================
# RANKING
# =========================================================

def top_total_users(limit=100):
    return db_execute(
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


def top_daily_users(limit=100):
    return db_execute(
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

def today_registered():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE DATE(created_at)=CURRENT_DATE
        """,
        fetchone=True,
    )
    return row[0]


def this_month_registered():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE DATE_TRUNC('month', created_at)=DATE_TRUNC('month', CURRENT_DATE)
        """,
        fetchone=True,
    )
    return row[0]


# =========================================================
# DASHBOARD
# =========================================================

def get_dashboard():
    return {
        "users": users_count(),
        "approved": approved_users_count(),
        "pending_users": pending_users_count(),

        "buyers": buyers_count(),
        "pending_payments": pending_payments_count(),
        "income": total_income(),

        "homeworks": homework_count(),
        "pending_homeworks": pending_homework_count(),

        "certificates": certificates_count(),

        "films": films_count(),
        "books": books_count(),
        "music": music_count(),
        "videos": videos_count(),

        "today": today_registered(),
        "month": this_month_registered(),
    }