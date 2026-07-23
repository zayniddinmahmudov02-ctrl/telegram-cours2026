from .connection import db_execute


# =========================================================
# CREATE
# =========================================================

def create_homework(
    user_id: int,
    level: str,
    lesson: int,
    homework_type: str,
    file_id: str,
):
    db_execute(
        """
        INSERT INTO homework
        (
            user_id,
            level,
            lesson,
            homework_type,
            file_id,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            'pending'
        )
        """,
        (
            user_id,
            level,
            lesson,
            homework_type,
            file_id,
        ),
    )


# =========================================================
# GET
# =========================================================

def get_homework(homework_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework
        WHERE id=%s
        """,
        (homework_id,),
        fetchone=True,
    )


def get_user_homeworks(user_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


def get_pending_homeworks():
    return db_execute(
        """
        SELECT *
        FROM homework
        WHERE status='pending'
        ORDER BY created_at
        """,
        fetchall=True,
    )


def get_checked_homeworks():
    return db_execute(
        """
        SELECT *
        FROM homework
        WHERE status='checked'
        ORDER BY checked_at DESC
        """,
        fetchall=True,
    )


# =========================================================
# STATUS
# =========================================================

def approve_homework(homework_id: int, score: int, comment: str):
    db_execute(
        """
        UPDATE homework
        SET
            status='checked',
            score=%s,
            teacher_comment=%s,
            checked_at=NOW()
        WHERE id=%s
        """,
        (
            score,
            comment,
            homework_id,
        ),
    )


def reject_homework(homework_id: int, comment: str):
    db_execute(
        """
        UPDATE homework
        SET
            status='rejected',
            teacher_comment=%s,
            checked_at=NOW()
        WHERE id=%s
        """,
        (
            comment,
            homework_id,
        ),
    )


# =========================================================
# DELETE
# =========================================================

def delete_homework(homework_id: int):
    db_execute(
        """
        DELETE
        FROM homework
        WHERE id=%s
        """,
        (homework_id,),
    )


# =========================================================
# STATISTICS
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


def pending_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM homework
        WHERE status='pending'
        """,
        fetchone=True,
    )

    return row[0]


def checked_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM homework
        WHERE status='checked'
        """,
        fetchone=True,
    )

    return row[0]