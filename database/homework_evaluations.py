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
