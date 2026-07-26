from .connection import db_execute


# =========================================================
# TABLE
# =========================================================

def create_tables():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework_files
        (
            id SERIAL PRIMARY KEY,

            submission_id INTEGER NOT NULL,

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
        idx_homework_files_submission
        ON homework_files(submission_id)
        """
    )


# =========================================================
# CREATE
# =========================================================

def add_file(
    submission_id: int,
    file_type: str,
    telegram_file_id: str | None = None,
    text_content: str | None = None,
):
    db_execute(
        """
        INSERT INTO homework_files
        (
            submission_id,
            file_type,
            telegram_file_id,
            text_content
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            submission_id,
            file_type,
            telegram_file_id,
            text_content,
        ),
    )


# =========================================================
# GET
# =========================================================

def get_files(submission_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_files
        WHERE submission_id=%s
        ORDER BY id
        """,
        (submission_id,),
        fetchall=True,
    )


def get_file(file_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_files
        WHERE id=%s
        """,
        (file_id,),
        fetchone=True,
    )


def files_count(submission_id: int):
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_files
        WHERE submission_id=%s
        """,
        (submission_id,),
        fetchone=True,
    )

    return row["count"]
# =========================================================
# FILTER
# =========================================================

def get_photos(submission_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_files
        WHERE
            submission_id=%s
            AND file_type='photo'
        ORDER BY id
        """,
        (submission_id,),
        fetchall=True,
    )


def get_documents(submission_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_files
        WHERE
            submission_id=%s
            AND file_type='document'
        ORDER BY id
        """,
        (submission_id,),
        fetchall=True,
    )


def get_audio(submission_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_files
        WHERE
            submission_id=%s
            AND file_type='audio'
        ORDER BY id
        """,
        (submission_id,),
        fetchall=True,
    )


def get_voice(submission_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_files
        WHERE
            submission_id=%s
            AND file_type='voice'
        ORDER BY id
        """,
        (submission_id,),
        fetchall=True,
    )


def get_text(submission_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_files
        WHERE
            submission_id=%s
            AND file_type='text'
        ORDER BY id
        """,
        (submission_id,),
        fetchall=True,
    )
# =========================================================
# DELETE
# =========================================================

def delete_file(file_id: int):
    db_execute(
        """
        DELETE
        FROM homework_files
        WHERE id=%s
        """,
        (file_id,),
    )


def delete_submission_files(submission_id: int):
    db_execute(
        """
        DELETE
        FROM homework_files
        WHERE submission_id=%s
        """,
        (submission_id,),
    )


# =========================================================
# STATISTICS
# =========================================================

def total_files():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_files
        """,
        fetchone=True,
    )

    return row["count"]


def photos_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_files
        WHERE file_type='photo'
        """,
        fetchone=True,
    )

    return row["count"]


def documents_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_files
        WHERE file_type='document'
        """,
        fetchone=True,
    )

    return row["count"]


def audio_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_files
        WHERE file_type='audio'
        """,
        fetchone=True,
    )

    return row["count"]


def voice_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_files
        WHERE file_type='voice'
        """,
        fetchone=True,
    )

    return row["count"]


def text_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_files
        WHERE file_type='text'
        """,
        fetchone=True,
    )

    return row["count"]
