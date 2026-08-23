from .connection import db_execute

# =========================================================
# UPSERT EVALUATION
# =========================================================
# UNIQUE(submission_id) on homework_evaluations (see database.init)
# means this is always "the current score" for that submission -
# re-scoring updates the same row in place instead of adding a
# second one, so SUM(score) elsewhere can never double-count.

async def save_evaluation(
    submission_id: int,
    score: int,
    result_status: str,
    evaluator_id: int,
):
    await db_execute(
        """
        INSERT INTO homework_evaluations
        (submission_id, score, result_status, evaluator_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (submission_id) DO UPDATE SET
            score=EXCLUDED.score,
            result_status=EXCLUDED.result_status,
            evaluator_id=EXCLUDED.evaluator_id,
            updated_at=NOW()
        """,
        (submission_id, score, result_status, evaluator_id),
    )


async def get_evaluation(submission_id: int):
    return await db_execute(
        """
        SELECT *
        FROM homework_evaluations
        WHERE submission_id=%s
        """,
        (submission_id,),
        fetchone=True,
    )


# =========================================================
# USER TOTALS
# =========================================================

async def get_user_score_summary(user_id: int):
    """
    Total score + evaluated count + average, plus a per-category
    breakdown, for the "🏆 Umumiy ball" screen. One evaluation row
    per submission (enforced by the UNIQUE constraint) means this
    SUM is always correct even after repeated re-scoring.
    """

    overall = await db_execute(
        """
        SELECT
            COALESCE(SUM(e.score), 0) AS total_score,
            COUNT(e.id) AS evaluated_count
        FROM homework_submissions s
        INNER JOIN homework_evaluations e ON e.submission_id = s.id
        WHERE s.user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )

    by_category = await db_execute(
        """
        SELECT
            c.id AS category_id,
            c.code,
            c.name AS category_name,
            COALESCE(SUM(e.score), 0) AS total_score,
            COUNT(e.id) AS evaluated_count
        FROM homework_categories c
        LEFT JOIN homework_submissions s
            ON s.category_id = c.id AND s.user_id = %s
        LEFT JOIN homework_evaluations e ON e.submission_id = s.id
        GROUP BY c.id, c.code, c.name
        HAVING COUNT(e.id) > 0
        ORDER BY c.id
        """,
        (user_id,),
        fetchall=True,
    )

    return {
        "total_score": overall["total_score"],
        "evaluated_count": overall["evaluated_count"],
        "average": (
            round(overall["total_score"] / overall["evaluated_count"], 1)
            if overall["evaluated_count"]
            else None
        ),
        "by_category": by_category,
    }


# =========================================================
# SPRECHEN PROGRESS (Sprechen guruh only)
# =========================================================
# Unlike get_user_score_summary (sums every evaluation ever, which
# is correct for Video/Online's open-ended submissions), Sprechen
# has a fixed 20-lesson grid where the SAME lesson can be
# resubmitted - only the most recent evaluated attempt per lesson
# may count, or a resubmission would double-count the total and a
# once-completed lesson could never reflect a corrected score.
# DISTINCT ON (Postgres-specific, used deliberately - this project
# is Postgres-only) with ORDER BY ... created_at DESC keeps exactly
# the latest evaluated submission per lesson_number.

async def get_sprechen_progress(user_id: int, category_id: int):
    return await db_execute(
        """
        SELECT DISTINCT ON (s.lesson_number)
            s.lesson_number,
            e.score,
            e.result_status
        FROM homework_submissions s
        INNER JOIN homework_evaluations e ON e.submission_id = s.id
        WHERE s.user_id=%s
        AND s.category_id=%s
        ORDER BY s.lesson_number, s.created_at DESC
        """,
        (user_id, category_id),
        fetchall=True,
    )


# =========================================================
# ADMIN - SPRECHEN STATISTICS (Sprechen guruh only)
# =========================================================
# Sprechen's `level` column holds the level_group code (see
# handlers.homework.sprechen) - grouped by that same column here.

async def get_sprechen_statistics(category_id: int):
    registration = await db_execute(
        """
        SELECT
            level_group,
            COUNT(*) AS registered,
            COUNT(*) FILTER (WHERE gender='male') AS male_count,
            COUNT(*) FILTER (WHERE gender='female') AS female_count
        FROM homework_memberships
        WHERE category_id=%s
        AND level_group IS NOT NULL
        GROUP BY level_group
        """,
        (category_id,),
        fetchall=True,
    )

    submissions = await db_execute(
        """
        SELECT
            level AS level_group,
            COUNT(*) AS submitted_count
        FROM homework_submissions
        WHERE category_id=%s
        AND status != 'draft'
        GROUP BY level
        """,
        (category_id,),
        fetchall=True,
    )

    # Latest evaluated submission per (user, lesson) - same
    # de-duplication logic as get_sprechen_progress, applied across
    # every member instead of one user, so a resubmission is never
    # counted twice in "completed" or "total score" here either.
    progress = await db_execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (s.user_id, s.lesson_number)
                s.user_id,
                s.lesson_number,
                s.level AS level_group,
                e.score
            FROM homework_submissions s
            INNER JOIN homework_evaluations e ON e.submission_id = s.id
            WHERE s.category_id=%s
            ORDER BY s.user_id, s.lesson_number, s.created_at DESC
        )
        SELECT
            level_group,
            COUNT(*) AS evaluated_count,
            COUNT(*) FILTER (WHERE score >= 4) AS completed_count,
            COALESCE(SUM(score), 0) AS total_score
        FROM latest
        GROUP BY level_group
        """,
        (category_id,),
        fetchall=True,
    )

    by_group = {}

    for row in registration:
        by_group[row["level_group"]] = {
            "level_group": row["level_group"],
            "registered": row["registered"],
            "male_count": row["male_count"],
            "female_count": row["female_count"],
            "submitted_count": 0,
            "evaluated_count": 0,
            "completed_count": 0,
            "total_score": 0,
        }

    for row in submissions:
        group = by_group.setdefault(
            row["level_group"],
            {
                "level_group": row["level_group"], "registered": 0,
                "male_count": 0, "female_count": 0, "submitted_count": 0,
                "evaluated_count": 0, "completed_count": 0, "total_score": 0,
            },
        )
        group["submitted_count"] = row["submitted_count"]

    for row in progress:
        group = by_group.setdefault(
            row["level_group"],
            {
                "level_group": row["level_group"], "registered": 0,
                "male_count": 0, "female_count": 0, "submitted_count": 0,
                "evaluated_count": 0, "completed_count": 0, "total_score": 0,
            },
        )
        group["evaluated_count"] = row["evaluated_count"]
        group["completed_count"] = row["completed_count"]
        group["total_score"] = row["total_score"]

    for group in by_group.values():
        group["average_score"] = (
            round(group["total_score"] / group["evaluated_count"], 1)
            if group["evaluated_count"]
            else None
        )

    overall = {
        "registered": sum(g["registered"] for g in by_group.values()),
        "male_count": sum(g["male_count"] for g in by_group.values()),
        "female_count": sum(g["female_count"] for g in by_group.values()),
        "submitted_count": sum(g["submitted_count"] for g in by_group.values()),
        "evaluated_count": sum(g["evaluated_count"] for g in by_group.values()),
        "completed_count": sum(g["completed_count"] for g in by_group.values()),
        "total_score": sum(g["total_score"] for g in by_group.values()),
    }
    overall["average_score"] = (
        round(overall["total_score"] / overall["evaluated_count"], 1)
        if overall["evaluated_count"]
        else None
    )

    return {"by_group": by_group, "overall": overall}


# =========================================================
# ADMIN STATISTICS
# =========================================================

async def get_homework_statistics():
    users = await db_execute(
        "SELECT COUNT(*) AS count FROM (SELECT DISTINCT user_id FROM homework_memberships) t",
        fetchone=True,
    )

    by_category = await db_execute(
        """
        SELECT
            c.id AS category_id,
            c.name AS category_name,
            COUNT(DISTINCT m.user_id) AS member_count
        FROM homework_categories c
        LEFT JOIN homework_memberships m ON m.category_id = c.id
        GROUP BY c.id, c.name
        ORDER BY c.id
        """,
        fetchall=True,
    )

    submissions = await db_execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE status != 'draft') AS total_submissions,
            COUNT(*) FILTER (WHERE status IN ('accepted', 'excellent', 'revision_required')) AS evaluated_submissions,
            COUNT(*) FILTER (WHERE status = 'submitted') AS pending_submissions
        FROM homework_submissions
        """,
        fetchone=True,
    )

    total_points = await db_execute(
        "SELECT COALESCE(SUM(score), 0) AS total FROM homework_evaluations",
        fetchone=True,
    )

    return {
        "total_users": users["count"],
        "by_category": by_category,
        "total_submissions": submissions["total_submissions"],
        "evaluated_submissions": submissions["evaluated_submissions"],
        "pending_submissions": submissions["pending_submissions"],
        "total_points": total_points["total"],
    }
