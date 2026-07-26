from .connection import db_execute


# =========================================================
# TABLES
# =========================================================

def create_tables():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework_submissions
        (
            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            course_type VARCHAR(20) NOT NULL,

            level VARCHAR(5) NOT NULL,

            lesson INTEGER NOT NULL,

            component VARCHAR(30) NOT NULL,

            task_number INTEGER,

            status VARCHAR(20)
                DEFAULT 'draft',

            score INTEGER,

            teacher_comment TEXT,

            checked_by BIGINT,

            checked_at TIMESTAMP,

            submitted_at TIMESTAMP,

            created_at TIMESTAMP
                DEFAULT NOW()
        )
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_homework_user
        ON homework_submissions(user_id)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_homework_status
        ON homework_submissions(status)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_homework_course
        ON homework_submissions(course_type)
        """
    )


# =========================================================
# CREATE
# =========================================================

def create_submission(
    user_id: int,
    course_type: str,
    level: str,
    lesson: int,
    component: str,
    task_number: int | None = None,
):
    db_execute(
        """
        INSERT INTO homework_submissions
        (
            user_id,
            course_type,
            level,
            lesson,
            component,
            task_number
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            user_id,
            course_type,
            level,
            lesson,
            component,
            task_number,
        ),
    )


# =========================================================
# GET
# =========================================================

def get_submission(submission_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE id=%s
        """,
        (submission_id,),
        fetchone=True,
    )


def get_user_submissions(user_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


def get_lesson_submissions(
    user_id: int,
    course_type: str,
    level: str,
    lesson: int,
):
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE
            user_id=%s
            AND course_type=%s
            AND level=%s
            AND lesson=%s
        ORDER BY id
        """,
        (
            user_id,
            course_type,
            level,
            lesson,
        ),
        fetchall=True,
    )


def submission_exists(
    user_id: int,
    course_type: str,
    level: str,
    lesson: int,
    component: str,
    task_number: int | None = None,
):
    row = db_execute(
        """
        SELECT id
        FROM homework_submissions
        WHERE
            user_id=%s
            AND course_type=%s
            AND level=%s
            AND lesson=%s
            AND component=%s
            AND
            (
                task_number IS NOT DISTINCT FROM %s
            )
        LIMIT 1
        """,
        (
            user_id,
            course_type,
            level,
            lesson,
            component,
            task_number,
        ),
        fetchone=True,
    )

    return bool(row)
# =========================================================
# UPDATE
# =========================================================

def update_status(
    submission_id: int,
    status: str,
):
    db_execute(
        """
        UPDATE homework_submissions
        SET status=%s
        WHERE id=%s
        """,
        (
            status,
            submission_id,
        ),
    )


def update_score(
    submission_id: int,
    score: int,
):
    db_execute(
        """
        UPDATE homework_submissions
        SET score=%s
        WHERE id=%s
        """,
        (
            score,
            submission_id,
        ),
    )


def update_teacher_comment(
    submission_id: int,
    comment: str,
):
    db_execute(
        """
        UPDATE homework_submissions
        SET teacher_comment=%s
        WHERE id=%s
        """,
        (
            comment,
            submission_id,
        ),
    )


def update_checked_by(
    submission_id: int,
    teacher_id: int,
):
    db_execute(
        """
        UPDATE homework_submissions
        SET checked_by=%s
        WHERE id=%s
        """,
        (
            teacher_id,
            submission_id,
        ),
    )


# =========================================================
# SUBMIT
# =========================================================

def submit_homework(
    submission_id: int,
):
    db_execute(
        """
        UPDATE homework_submissions
        SET
            status='submitted',
            submitted_at=NOW()
        WHERE id=%s
        """,
        (
            submission_id,
        ),
    )


# =========================================================
# CHECK
# =========================================================

def approve_submission(
    submission_id: int,
    score: int,
    teacher_comment: str,
    teacher_id: int,
):
    db_execute(
        """
        UPDATE homework_submissions
        SET
            status='checked',
            score=%s,
            teacher_comment=%s,
            checked_by=%s,
            checked_at=NOW()
        WHERE id=%s
        """,
        (
            score,
            teacher_comment,
            teacher_id,
            submission_id,
        ),
    )


def reject_submission(
    submission_id: int,
    teacher_comment: str,
    teacher_id: int,
):
    db_execute(
        """
        UPDATE homework_submissions
        SET
            status='rejected',
            teacher_comment=%s,
            checked_by=%s,
            checked_at=NOW()
        WHERE id=%s
        """,
        (
            teacher_comment,
            teacher_id,
            submission_id,
        ),
    )


# =========================================================
# DELETE
# =========================================================

def delete_submission(
    submission_id: int,
):
    db_execute(
        """
        DELETE
        FROM homework_submissions
        WHERE id=%s
        """,
        (
            submission_id,
        ),
    )


def delete_lesson(
    user_id: int,
    course_type: str,
    level: str,
    lesson: int,
):
    db_execute(
        """
        DELETE
        FROM homework_submissions
        WHERE
            user_id=%s
            AND course_type=%s
            AND level=%s
            AND lesson=%s
        """,
        (
            user_id,
            course_type,
            level,
            lesson,
        ),
    )
# =========================================================
# ADMIN
# =========================================================

def get_pending_submissions():
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE status='submitted'
        ORDER BY submitted_at
        """,
        fetchall=True,
    )


def get_checked_submissions():
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE status='checked'
        ORDER BY checked_at DESC
        """,
        fetchall=True,
    )


def get_rejected_submissions():
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE status='rejected'
        ORDER BY checked_at DESC
        """,
        fetchall=True,
    )


def get_draft_submissions():
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE status='draft'
        ORDER BY created_at DESC
        """,
        fetchall=True,
    )


# =========================================================
# FILTER
# =========================================================

def get_level_submissions(level: str):
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE level=%s
        ORDER BY created_at DESC
        """,
        (level,),
        fetchall=True,
    )


def get_course_submissions(course_type: str):
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE course_type=%s
        ORDER BY created_at DESC
        """,
        (course_type,),
        fetchall=True,
    )


def get_component_submissions(component: str):
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE component=%s
        ORDER BY created_at DESC
        """,
        (component,),
        fetchall=True,
    )


# =========================================================
# COUNTS
# =========================================================

def submissions_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submissions
        """,
        fetchone=True,
    )

    return row["count"]


def pending_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submissions
        WHERE status='submitted'
        """,
        fetchone=True,
    )

    return row["count"]


def checked_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submissions
        WHERE status='checked'
        """,
        fetchone=True,
    )

    return row["count"]


def rejected_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submissions
        WHERE status='rejected'
        """,
        fetchone=True,
    )

    return row["count"]


def draft_count():
    row = db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submissions
        WHERE status='draft'
        """,
        fetchone=True,
    )

    return row["count"]


# =========================================================
# USER HELPERS
# =========================================================

def get_last_submission(user_id: int):
    return db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,),
        fetchone=True,
    )


def has_pending_submission(user_id: int):
    row = db_execute(
        """
        SELECT id
        FROM homework_submissions
        WHERE
            user_id=%s
            AND status='submitted'
        LIMIT 1
        """,
        (user_id,),
        fetchone=True,
    )

    return bool(row)


def has_draft_submission(user_id: int):
    row = db_execute(
        """
        SELECT id
        FROM homework_submissions
        WHERE
            user_id=%s
            AND status='draft'
        LIMIT 1
        """,
        (user_id,),
        fetchone=True,
    )

    return bool(row)


# =========================================================
# DASHBOARD
# =========================================================

def dashboard_statistics():
    return {
        "total": submissions_count(),
        "draft": draft_count(),
        "submitted": pending_count(),
        "checked": checked_count(),
        "rejected": rejected_count(),
    }