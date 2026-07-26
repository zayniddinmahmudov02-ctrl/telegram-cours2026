from .connection import db_execute


# =========================================================
# TABLES
# =========================================================

def create_tables():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_messages
        (
            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            status VARCHAR(20)
                DEFAULT 'pending',

            admin_id BIGINT,

            reply_text TEXT,

            replied_at TIMESTAMP,

            created_at TIMESTAMP
                DEFAULT NOW()
        )
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_teacher_messages_user
        ON teacher_messages(user_id)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_teacher_messages_status
        ON teacher_messages(status)
        """
    )


# =========================================================
# CREATE
# =========================================================

def create_message(user_id: int):
    db_execute(
        """
        INSERT INTO teacher_messages
        (
            user_id
        )
        VALUES
        (
            %s
        )
        """,
        (
            user_id,
        ),
    )


# =========================================================
# GET
# =========================================================

def get_message(message_id: int):
    return db_execute(
        """
        SELECT *
        FROM teacher_messages
        WHERE id=%s
        """,
        (message_id,),
        fetchone=True,
    )


def get_user_messages(user_id: int):
    return db_execute(
        """
        SELECT *
        FROM teacher_messages
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


def get_pending_messages():
    return db_execute(
        """
        SELECT *
        FROM teacher_messages
        WHERE status='pending'
        ORDER BY created_at
        """,
        fetchall=True,
    )
# =========================================================
# REPLY
# =========================================================

def reply_message(
    message_id: int,
    admin_id: int,
    reply_text: str,
):
    db_execute(
        """
        UPDATE teacher_messages
        SET
            status='answered',
            admin_id=%s,
            reply_text=%s,
            replied_at=NOW()
        WHERE id=%s
        """,
        (
            admin_id,
            reply_text,
            message_id,
        ),
    )


def close_message(message_id: int):
    db_execute(
        """
        UPDATE teacher_messages
        SET status='closed'
        WHERE id=%s
        """,
        (
            message_id,
        ),
    )


def reopen_message(message_id: int):
    db_execute(
        """
        UPDATE teacher_messages
        SET status='pending'
        WHERE id=%s
        """,
        (
            message_id,
        ),
    )
# =========================================================
# DAILY LIMIT
# =========================================================

def today_messages_count(user_id: int):
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_messages
        WHERE
            user_id=%s
            AND DATE(created_at)=CURRENT_DATE
        """,
        (
            user_id,
        ),
        fetchone=True,
    )

    return row["count"]


def can_send_today(user_id: int):
    return today_messages_count(user_id) < 3


# =========================================================
# DELETE
# =========================================================

def delete_message(message_id: int):
    db_execute(
        """
        DELETE
        FROM teacher_messages
        WHERE id=%s
        """,
        (
            message_id,
        ),
    )


# =========================================================
# STATISTICS
# =========================================================

def total_messages():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_messages
        """,
        fetchone=True,
    )

    return row["count"]


def pending_messages_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_messages
        WHERE status='pending'
        """,
        fetchone=True,
    )

    return row["count"]


def answered_messages_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_messages
        WHERE status='answered'
        """,
        fetchone=True,
    )

    return row["count"]
