from .connection import db_execute


# =========================================================
# TABLE
# =========================================================

def create_tables():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_message_files
        (
            id SERIAL PRIMARY KEY,

            message_id INTEGER NOT NULL,

            sender VARCHAR(20) NOT NULL,

            file_type VARCHAR(20) NOT NULL,

            telegram_file_id TEXT,

            text_content TEXT,

            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_teacher_files_message
        ON teacher_message_files(message_id)
        """
    )


# =========================================================
# CREATE
# =========================================================

def add_file(
    message_id: int,
    sender: str,
    file_type: str,
    telegram_file_id: str | None = None,
    text_content: str | None = None,
):
    db_execute(
        """
        INSERT INTO teacher_message_files
        (
            message_id,
            sender,
            file_type,
            telegram_file_id,
            text_content
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            message_id,
            sender,
            file_type,
            telegram_file_id,
            text_content,
        ),
    )
# =========================================================
# GET
# =========================================================

def get_files(message_id: int):
    return db_execute(
        """
        SELECT *
        FROM teacher_message_files
        WHERE message_id=%s
        ORDER BY id
        """,
        (message_id,),
        fetchall=True,
    )


def get_file(file_id: int):
    return db_execute(
        """
        SELECT *
        FROM teacher_message_files
        WHERE id=%s
        """,
        (file_id,),
        fetchone=True,
    )


def get_student_files(message_id: int):
    return db_execute(
        """
        SELECT *
        FROM teacher_message_files
        WHERE
            message_id=%s
            AND sender='student'
        ORDER BY id
        """,
        (message_id,),
        fetchall=True,
    )


def get_teacher_files(message_id: int):
    return db_execute(
        """
        SELECT *
        FROM teacher_message_files
        WHERE
            message_id=%s
            AND sender='teacher'
        ORDER BY id
        """,
        (message_id,),
        fetchall=True,
    )
# =========================================================
# DELETE
# =========================================================

def delete_file(file_id: int):
    db_execute(
        """
        DELETE
        FROM teacher_message_files
        WHERE id=%s
        """,
        (file_id,),
    )


def delete_message_files(message_id: int):
    db_execute(
        """
        DELETE
        FROM teacher_message_files
        WHERE message_id=%s
        """,
        (message_id,),
    )


# =========================================================
# STATISTICS
# =========================================================

def total_files():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_message_files
        """,
        fetchone=True,
    )

    return row["count"]


def files_count(message_id: int):
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_message_files
        WHERE message_id=%s
        """,
        (message_id,),
        fetchone=True,
    )

    return row["count"]


def student_files_count(message_id: int):
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_message_files
        WHERE
            message_id=%s
            AND sender='student'
        """,
        (message_id,),
        fetchone=True,
    )

    return row["count"]


def teacher_files_count(message_id: int):
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM teacher_message_files
        WHERE
            message_id=%s
            AND sender='teacher'
        """,
        (message_id,),
        fetchone=True,
    )

    return row["count"]
