import secrets

from .connection import db_execute

# =========================================================
# SUBMISSION UID
# =========================================================

def generate_submission_uid() -> str:
    return "HW-" + secrets.token_hex(4).upper()


# =========================================================
# DRAFT LIFECYCLE
# =========================================================
# A submission is a "draft" (status='draft') while the user is
# still uploading files. get_or_create_draft is the single entry
# point for "📤 Vazifa yuborish" - it resumes an existing draft
# instead of creating a new one, which is what makes the flow
# survive a bot restart (FSM storage is in-memory - see loader.py -
# but the draft row and its files are not).

async def get_draft_submission(user_id: int, category_id: int):
    return await db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE user_id=%s
        AND category_id=%s
        AND status='draft'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, category_id),
        fetchone=True,
    )


async def create_draft_submission(
    user_id: int,
    category_id: int,
    first_name: str,
    last_name: str,
    level: str,
    lesson_number: int,
):
    row = await db_execute(
        """
        INSERT INTO homework_submissions
        (
            submission_uid, user_id, category_id,
            first_name, last_name, level, lesson_number,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft')
        RETURNING id, submission_uid;
        """,
        (
            generate_submission_uid(),
            user_id,
            category_id,
            first_name,
            last_name,
            level,
            lesson_number,
        ),
        fetchone=True,
    )

    return row


async def get_or_create_draft_submission(
    user_id: int,
    category_id: int,
    first_name: str,
    last_name: str,
    level: str,
    lesson_number: int,
):
    draft = await get_draft_submission(user_id, category_id)

    if draft:
        return draft

    row = await create_draft_submission(
        user_id, category_id, first_name, last_name, level, lesson_number
    )

    return await get_submission(row["id"])


async def delete_draft_submission(submission_id: int):
    """
    Cancels/removes an unsubmitted draft (and its files, via
    ON DELETE CASCADE) - does nothing if the submission was
    already confirmed, so a stray cancel can never delete a real
    submission.
    """

    await db_execute(
        """
        DELETE FROM homework_submissions
        WHERE id=%s
        AND status='draft'
        """,
        (submission_id,),
    )


# =========================================================
# FILES
# =========================================================

async def add_submission_file(
    submission_id: int,
    file_type: str,
    file_id: str | None = None,
    file_name: str | None = None,
    mime_type: str | None = None,
    file_size: int | None = None,
    text_content: str | None = None,
):
    row = await db_execute(
        """
        INSERT INTO homework_submission_files
        (
            submission_id, file_type, file_id,
            file_name, mime_type, file_size, text_content,
            file_position
        )
        VALUES (
            %(submission_id)s, %(file_type)s, %(file_id)s,
            %(file_name)s, %(mime_type)s, %(file_size)s, %(text_content)s,
            COALESCE(
                (SELECT MAX(file_position) + 1 FROM homework_submission_files
                 WHERE submission_id = %(submission_id)s),
                0
            )
        )
        RETURNING id;
        """,
        {
            "submission_id": submission_id,
            "file_type": file_type,
            "file_id": file_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_size": file_size,
            "text_content": text_content,
        },
        fetchone=True,
    )

    return row["id"]


async def get_submission_files(submission_id: int):
    return await db_execute(
        """
        SELECT *
        FROM homework_submission_files
        WHERE submission_id=%s
        ORDER BY file_position
        """,
        (submission_id,),
        fetchall=True,
    )


async def count_submission_files(submission_id: int) -> int:
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submission_files
        WHERE submission_id=%s
        """,
        (submission_id,),
        fetchone=True,
    )

    return row["count"]


# =========================================================
# READ
# =========================================================

async def get_submission(submission_id: int):
    return await db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE id=%s
        """,
        (submission_id,),
        fetchone=True,
    )


async def get_submission_by_uid(submission_uid: str):
    return await db_execute(
        """
        SELECT *
        FROM homework_submissions
        WHERE submission_uid=%s
        """,
        (submission_uid,),
        fetchone=True,
    )


async def get_user_submissions(
    user_id: int,
    category_id: int,
    statuses: tuple[str, ...],
    limit: int = 10,
    offset: int = 0,
):
    return await db_execute(
        """
        SELECT
            s.*,
            e.score,
            e.result_status
        FROM homework_submissions s
        LEFT JOIN homework_evaluations e ON e.submission_id = s.id
        WHERE s.user_id=%(user_id)s
        AND s.category_id=%(category_id)s
        AND s.status = ANY(%(statuses)s)
        ORDER BY s.created_at DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {
            "user_id": user_id,
            "category_id": category_id,
            "statuses": list(statuses),
            "limit": limit,
            "offset": offset,
        },
        fetchall=True,
    )


async def count_user_submissions(
    user_id: int,
    category_id: int,
    statuses: tuple[str, ...],
) -> int:
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submissions
        WHERE user_id=%(user_id)s
        AND category_id=%(category_id)s
        AND status = ANY(%(statuses)s)
        """,
        {
            "user_id": user_id,
            "category_id": category_id,
            "statuses": list(statuses),
        },
        fetchone=True,
    )

    return row["count"]


# =========================================================
# WRITE - LIFECYCLE
# =========================================================

async def claim_submission_for_confirm(submission_id: int) -> bool:
    """
    Atomically flips draft -> submitted BEFORE anything is sent to
    the channel. This (not the status check in the handler) is what
    actually prevents a double-tap on "Tasdiqlash" from producing
    two channel posts: the handler's earlier read-then-act check has
    several `await`s (Telegram API calls) between reading the status
    and recording it, so two near-simultaneous taps could both pass
    that check. Only the first UPDATE that finds status='draft' wins
    (returns the row); a concurrent/duplicate call sees status
    already changed and gets nothing back, so it must not send
    anything.
    """

    row = await db_execute(
        """
        UPDATE homework_submissions
        SET status='submitted', submitted_at=NOW()
        WHERE id=%s
        AND status='draft'
        RETURNING id
        """,
        (submission_id,),
        fetchone=True,
    )

    return row is not None


async def revert_submission_to_draft(submission_id: int):
    """
    Undoes claim_submission_for_confirm() when the channel send that
    was supposed to follow it fails, so the user can retry instead
    of being stuck on a 'submitted' row with nothing actually posted.
    """

    await db_execute(
        """
        UPDATE homework_submissions
        SET status='draft', submitted_at=NULL
        WHERE id=%s
        """,
        (submission_id,),
    )


async def set_submission_channel_message(
    submission_id: int,
    channel_id: int,
    channel_message_id: int,
):
    await db_execute(
        """
        UPDATE homework_submissions
        SET channel_id=%s, channel_message_id=%s
        WHERE id=%s
        """,
        (channel_id, channel_message_id, submission_id),
    )


async def set_submission_status(submission_id: int, status: str):
    await db_execute(
        """
        UPDATE homework_submissions
        SET
            status=%s,
            evaluated_at=NOW()
        WHERE id=%s
        """,
        (status, submission_id),
    )


# =========================================================
# ADMIN - BROWSING / FILTERING
# =========================================================

async def search_submissions(
    category_id: int | None = None,
    level: str | None = None,
    lesson_number: int | None = None,
    user_id: int | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    return await db_execute(
        """
        SELECT
            s.*,
            c.name AS category_name,
            e.score,
            e.result_status
        FROM homework_submissions s
        INNER JOIN homework_categories c ON c.id = s.category_id
        LEFT JOIN homework_evaluations e ON e.submission_id = s.id
        WHERE s.status != 'draft'
        AND (%(category_id)s IS NULL OR s.category_id = %(category_id)s)
        AND (%(level)s IS NULL OR s.level = %(level)s)
        AND (%(lesson_number)s IS NULL OR s.lesson_number = %(lesson_number)s)
        AND (%(user_id)s IS NULL OR s.user_id = %(user_id)s)
        AND (%(status)s IS NULL OR s.status = %(status)s)
        ORDER BY s.created_at DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {
            "category_id": category_id,
            "level": level,
            "lesson_number": lesson_number,
            "user_id": user_id,
            "status": status,
            "limit": limit,
            "offset": offset,
        },
        fetchall=True,
    )


async def count_submissions(
    category_id: int | None = None,
    level: str | None = None,
    lesson_number: int | None = None,
    user_id: int | None = None,
    status: str | None = None,
) -> int:
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM homework_submissions s
        WHERE s.status != 'draft'
        AND (%(category_id)s IS NULL OR s.category_id = %(category_id)s)
        AND (%(level)s IS NULL OR s.level = %(level)s)
        AND (%(lesson_number)s IS NULL OR s.lesson_number = %(lesson_number)s)
        AND (%(user_id)s IS NULL OR s.user_id = %(user_id)s)
        AND (%(status)s IS NULL OR s.status = %(status)s)
        """,
        {
            "category_id": category_id,
            "level": level,
            "lesson_number": lesson_number,
            "user_id": user_id,
            "status": status,
        },
        fetchone=True,
    )

    return row["count"]
