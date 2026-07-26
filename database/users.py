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

    return row["full_name"] if row else None


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

    return row["phone"] if row else None


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

    return bool(row["approved"]) if row else False


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

    return row["unlocked_level"] if row else "A1"
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


def block_user(user_id: int):
    db_execute(
        """
        UPDATE users
        SET is_blocked=TRUE
        WHERE user_id=%s
        """,
        (user_id,),
    )


def unblock_user(user_id: int):
    db_execute(
        """
        UPDATE users
        SET is_blocked=FALSE
        WHERE user_id=%s
        """,
        (user_id,),
    )
# =========================================================
# STATISTICS
# =========================================================

def users_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        """,
        fetchone=True,
    )

    return row["count"]


def approved_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE approved=TRUE
        """,
        fetchone=True,
    )

    return row["count"]


def blocked_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE is_blocked=TRUE
        """,
        fetchone=True,
    )

    return row["count"]


def pending_users():
    return db_execute(
        """
        SELECT
            user_id,
            full_name,
            approved
        FROM users
        WHERE approved=FALSE
        ORDER BY id DESC
        """,
        fetchall=True,
    )


# =========================================================
# ADMIN HELPERS
# =========================================================

def get_total_users():
    return users_count()


def get_approved_users():
    return approved_count()


def get_blocked_users():
    return blocked_count()


def get_latest_users(limit: int = 10):
    return db_execute(
        """
        SELECT
            user_id,
            full_name,
            approved,
            is_blocked
        FROM users
        ORDER BY id DESC
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
        SELECT
            user_id,
            full_name
        FROM users
        WHERE is_blocked=FALSE
        ORDER BY id
        """,
        fetchall=True,
    )