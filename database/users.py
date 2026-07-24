from .connection import db_execute


# =========================================================
# CREATE
# =========================================================

def create_user(user_id: int, full_name: str):
    db_execute(
        """
        INSERT INTO users
        (
            user_id,
            full_name,
            approved,
            unlocked_level
        )
        VALUES
        (
            %s,
            %s,
            FALSE,
            'A1'
        )
        ON CONFLICT(user_id)
        DO UPDATE SET
            full_name = EXCLUDED.full_name
        """,
        (user_id, full_name),
    )


# =========================================================
# GET
# =========================================================

def get_user(user_id: int):
    return db_execute(
        """
        SELECT *
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )


def user_exists(user_id: int):
    return db_execute(
        """
        SELECT 1
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    ) is not None


def get_full_name(user_id: int):
    row = db_execute(
        """
        SELECT full_name
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )

    return row[0] if row else None


def get_phone(user_id: int):
    row = db_execute(
        """
        SELECT phone
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )

    return row[0] if row else None


def is_approved(user_id: int):
    row = db_execute(
        """
        SELECT approved
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )

    return bool(row[0]) if row else False


def get_unlocked_level(user_id: int):
    row = db_execute(
        """
        SELECT unlocked_level
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )

    return row[0] if row else "A1"


# =========================================================
# UPDATE
# =========================================================

def update_full_name(user_id: int, full_name: str):
    db_execute(
        """
        UPDATE users
        SET full_name=%s
        WHERE user_id=%s
        """,
        (full_name, user_id),
    )


def update_phone(user_id: int, phone: str):
    db_execute(
        """
        UPDATE users
        SET phone=%s
        WHERE user_id=%s
        """,
        (phone, user_id),
    )


def approve_user(user_id: int):
    db_execute(
        """
        UPDATE users
        SET approved=TRUE
        WHERE user_id=%s
        """,
        (user_id,),
    )


def reject_user(user_id: int):
    db_execute(
        """
        UPDATE users
        SET approved=FALSE
        WHERE user_id=%s
        """,
        (user_id,),
    )


def update_unlocked_level(user_id: int, level: str):
    db_execute(
        """
        UPDATE users
        SET unlocked_level=%s
        WHERE user_id=%s
        """,
        (level, user_id),
    )


# =========================================================
# SCORE
# =========================================================

def add_total_score(user_id: int, score: int):
    db_execute(
        """
        UPDATE users
        SET total_score =
            COALESCE(total_score,0)+%s
        WHERE user_id=%s
        """,
        (score, user_id),
    )


def add_daily_score(user_id: int, score: int):
    db_execute(
        """
        UPDATE users
        SET daily_score =
            COALESCE(daily_score,0)+%s
        WHERE user_id=%s
        """,
        (score, user_id),
    )


def reset_daily_scores(today):
    db_execute(
        """
        UPDATE users
        SET
            daily_score=0,
            last_daily_reset=%s
        WHERE
            last_daily_reset IS NULL
            OR last_daily_reset<%s
        """,
        (today, today),
    )


# =========================================================
# STATISTICS
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


def approved_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE approved=TRUE
        """,
        fetchone=True,
    )

    return row[0]


def pending_users():
    return db_execute(
        """
        SELECT *
        FROM users
        WHERE approved=FALSE
        ORDER BY user_id DESC
        """,
        fetchall=True,
    )


def top_total(limit=100):
    return db_execute(
        """
        SELECT full_name,total_score
        FROM users
        WHERE approved=TRUE
        ORDER BY total_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


def top_daily(limit=100):
    return db_execute(
        """
        SELECT full_name,daily_score
        FROM users
        WHERE approved=TRUE
        ORDER BY daily_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )
# =========================================================
# ALL USERS
# =========================================================

def get_all_users():

    return db_execute(
        """
        SELECT user_id
        FROM users
        WHERE is_blocked=FALSE
        ORDER BY id
        """,
        fetchall=True,
    )