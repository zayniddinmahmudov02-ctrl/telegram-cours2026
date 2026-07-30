from config import APP_TIMEZONE

from .connection import db_execute


def _period_start_sql(trunc: str) -> str:
    """
    SQL expression for the start of the current day/week/month
    in APP_TIMEZONE, as an absolute instant (timestamptz) that
    can be compared directly against xp_events.created_at
    (also timestamptz) - correct regardless of whatever
    timezone the database server itself is configured with.

    Postgres truncates 'week' to Monday 00:00, matching the
    Mon-Sun week definition.
    """

    return (
        f"date_trunc('{trunc}', NOW() AT TIME ZONE '{APP_TIMEZONE}') "
        f"AT TIME ZONE '{APP_TIMEZONE}'"
    )

# =========================================================
# CREATE
# =========================================================

def create_user_score(user_id: int):
    """
    Create score record for a new player.
    """

    db_execute(
        """
        INSERT INTO user_scores
        (
            user_id
        )
        VALUES
        (
            %s
        )
        ON CONFLICT (user_id)
        DO NOTHING
        """,
        (user_id,),
    )


# =========================================================
# UPDATE SCORE
# =========================================================

def add_score(user_id: int, points: int):
    """
    Record an XP gain.

    global_score is a running, never-reset lifetime total
    (Overall Ranking). xp_events is a timestamped ledger of
    every XP-earning event, used to compute Daily/Weekly/
    Monthly rankings by filtering on created_at instead of
    periodically resetting a counter.
    """

    create_user_score(user_id)

    db_execute(
        """
        UPDATE user_scores
        SET
            global_score = global_score + %s,

            correct_answers = correct_answers + 1,

            updated_at = NOW()

        WHERE user_id = %s
        """,
        (
            points,
            user_id,
        ),
    )

    db_execute(
        """
        INSERT INTO xp_events
        (
            user_id,
            xp
        )
        VALUES
        (
            %s,
            %s
        )
        """,
        (
            user_id,
            points,
        ),
    )


def add_wrong_answer(user_id: int):
    """
    Increase wrong answer counter.
    """

    create_user_score(user_id)

    db_execute(
        """
        UPDATE user_scores
        SET
            wrong_answers = wrong_answers + 1,
            updated_at = NOW()

        WHERE user_id = %s
        """,
        (user_id,),
    )
# =========================================================
# GETTERS
# =========================================================

def get_user_score(user_id: int):
    return db_execute(
        """
        SELECT
            *
        FROM user_scores
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )


# =========================================================
# TOP RANKINGS
# =========================================================
# Daily/Weekly/Monthly are computed by filtering the xp_events
# ledger on created_at - nothing is ever reset. Boundaries are
# computed in APP_TIMEZONE (see _period_start_sql above), so
# "today"/"this week"/"this month" match the real local day
# regardless of the database server's own timezone setting
# ('week' truncates to Monday 00:00, matching Mon-Sun weeks).
# Global/Overall reuses user_scores.global_score, a running
# lifetime total that is never reset either.

PERIOD_TRUNC = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
}


def get_top(period: str, limit: int = 100):

    if period == "global":
        return db_execute(
            """
            SELECT
                u.user_id,
                u.full_name,
                s.global_score
            FROM user_scores s
            INNER JOIN users u
                ON u.user_id = s.user_id
            WHERE
                u.is_blocked = FALSE
            ORDER BY s.global_score DESC
            LIMIT %s
            """,
            (limit,),
            fetchall=True,
        )

    trunc = PERIOD_TRUNC.get(period)

    if not trunc:
        return []

    score_field = f"{period}_score"
    period_start = _period_start_sql(trunc)

    return db_execute(
        f"""
        SELECT
            u.user_id,
            u.full_name,
            COALESCE(SUM(e.xp), 0) AS {score_field}
        FROM xp_events e
        INNER JOIN users u
            ON u.user_id = e.user_id
        WHERE
            e.created_at >= {period_start}
            AND u.is_blocked = FALSE
        GROUP BY u.user_id, u.full_name
        ORDER BY {score_field} DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


def get_daily_top(limit: int = 100):
    return get_top("daily", limit)


def get_weekly_top(limit: int = 100):
    return get_top("weekly", limit)


def get_monthly_top(limit: int = 100):
    return get_top("monthly", limit)


def get_global_top(limit: int = 100):
    return get_top("global", limit)


def get_overall_top(limit: int = 100):
    """
    Overall Ranking: lifetime XP (never resets) plus average
    accuracy across every completed Word Game block, taken
    directly from quiz_progress.best_score (real per-block
    scores, not an estimate - never XP).

    avg_accuracy is NULL (not 0) when the user has never
    completed a block, and rounded to at most one decimal
    place, e.g. 91.8 rather than 91.833333333333333.
    """

    return db_execute(
        """
        SELECT
            u.user_id,
            u.full_name,
            s.global_score AS total_xp,
            (
                SELECT ROUND(AVG(qp.best_score)::numeric, 1)
                FROM quiz_progress qp
                WHERE qp.user_id = u.user_id
            ) AS avg_accuracy
        FROM user_scores s
        INNER JOIN users u
            ON u.user_id = s.user_id
        WHERE
            u.is_blocked = FALSE
        ORDER BY s.global_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


# =========================================================
# USER RANK
# =========================================================

def get_user_rank(user_id: int, period: str):

    if period == "global":

        row = db_execute(
            """
            SELECT rank
            FROM
            (
                SELECT
                    user_id,
                    RANK() OVER(
                        ORDER BY global_score DESC
                    ) AS rank
                FROM user_scores
            ) ranks
            WHERE user_id = %s
            """,
            (user_id,),
            fetchone=True,
        )

        return row["rank"] if row else None

    trunc = PERIOD_TRUNC.get(period)

    if not trunc:
        return None

    period_start = _period_start_sql(trunc)

    row = db_execute(
        f"""
        SELECT rank
        FROM
        (
            SELECT
                user_id,
                RANK() OVER(
                    ORDER BY SUM(xp) DESC
                ) AS rank
            FROM xp_events
            WHERE created_at >= {period_start}
            GROUP BY user_id
        ) ranks
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )

    return row["rank"] if row else None


# =========================================================
# PERIOD CHAMPION (for schedulers)
# =========================================================

def get_period_champion(start, end):
    """
    Highest XP earner strictly within [start, end) - used to
    determine the winner of a week/month that just ended.
    """

    return db_execute(
        """
        SELECT
            u.user_id,
            u.full_name,
            COALESCE(SUM(e.xp), 0) AS score
        FROM xp_events e
        INNER JOIN users u
            ON u.user_id = e.user_id
        WHERE
            e.created_at >= %s
            AND e.created_at < %s
        GROUP BY u.user_id, u.full_name
        ORDER BY score DESC
        LIMIT 1
        """,
        (start, end),
        fetchone=True,
    )
# =========================================================
# CHAMPIONS
# =========================================================

def save_weekly_champion(
    year: int,
    week: int,
    user_id: int,
    score: int,
):
    db_execute(
        """
        INSERT INTO weekly_champions
        (
            year,
            week,
            user_id,
            full_name,
            score
        )
        SELECT
            %s,
            %s,
            u.user_id,
            u.full_name,
            %s
        FROM users u
        WHERE u.user_id = %s
        """,
        (
            year,
            week,
            score,
            user_id,
        ),
    )


def save_monthly_champion(
    year: int,
    month: int,
    user_id: int,
    score: int,
):
    db_execute(
        """
        INSERT INTO monthly_champions
        (
            year,
            month,
            user_id,
            full_name,
            score
        )
        SELECT
            %s,
            %s,
            u.user_id,
            u.full_name,
            %s
        FROM users u
        WHERE u.user_id = %s
        """,
        (
            year,
            month,
            score,
            user_id,
        ),
    )


def get_monthly_champions(year: int):
    return db_execute(
        """
        SELECT
            *
        FROM monthly_champions
        WHERE year = %s
        ORDER BY month
        """,
        (year,),
        fetchall=True,
    )


def get_weekly_champions(year: int):
    return db_execute(
        """
        SELECT
            *
        FROM weekly_champions
        WHERE year = %s
        ORDER BY week
        """,
        (year,),
        fetchall=True,
    )


def get_recent_weekly_champions(limit: int = 20):
    """
    Most recent weekly champions, newest first. Weekly
    history spans many more entries than monthly, so it is
    browsed as a flat recent list instead of a year picker.
    """

    return db_execute(
        """
        SELECT
            *
        FROM weekly_champions
        ORDER BY year DESC, week DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


# =========================================================
# HALL OF FAME
# =========================================================

def save_hall_of_fame(
    year: int,
    month: int,
    champion_id: int,
):
    db_execute(
        """
        INSERT INTO hall_of_fame
        (
            year,
            month,
            champion_id
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
        """,
        (
            year,
            month,
            champion_id,
        ),
    )


def get_hall_of_fame(year: int):
    return db_execute(
        """
        SELECT
            h.year,
            h.month,
            c.user_id,
            c.full_name,
            c.score
        FROM hall_of_fame h
        INNER JOIN monthly_champions c
            ON h.champion_id = c.id
        WHERE h.year = %s
        ORDER BY h.month
        """,
        (year,),
        fetchall=True,
    )
# =========================================================
# STATISTICS
# =========================================================

def get_total_players():
    row = db_execute(
        """
        SELECT COUNT(*) AS total
        FROM user_scores
        """,
        fetchone=True,
    )

    return row["total"] if row else 0


def get_top_player(period: str):

    columns = {
        "daily": "daily_score",
        "weekly": "weekly_score",
        "monthly": "monthly_score",
        "global": "global_score",
    }

    column = columns.get(period)

    if not column:
        return None

    return db_execute(
        f"""
        SELECT
            u.user_id,
            u.full_name,
            s.daily_score,
            s.weekly_score,
            s.monthly_score,
            s.global_score,
            s.correct_answers,
            s.wrong_answers
        FROM user_scores s
        INNER JOIN users u
            ON u.user_id = s.user_id
        WHERE
         u.is_blocked = FALSE
        ORDER BY s.{column} DESC
        LIMIT 1
        """,
        fetchone=True,
    )


def get_user_statistics(user_id: int):
    return db_execute(
        """
        SELECT
            daily_score,
            weekly_score,
            monthly_score,
            global_score,
            correct_answers,
            wrong_answers,
            current_streak,
            best_streak
        FROM user_scores
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )


def get_accuracy(user_id: int):
    """
    Average accuracy (%) across every completed Word Game
    block, taken directly from quiz_progress.best_score
    (each block is scored out of 100, so best_score already
    is a percentage) - real statistics, never XP, never an
    estimate.

    Returns None (display as "-", never "0%") if the user has
    not completed a single block yet.
    """

    row = db_execute(
        """
        SELECT AVG(best_score) AS avg_score
        FROM quiz_progress
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )

    if not row or row["avg_score"] is None:
        return None

    return round(float(row["avg_score"]), 1)


# =========================================================
# USER XP SUMMARY (PROFILE)
# =========================================================

def get_user_xp_summary(user_id: int) -> dict:
    """
    Today/this-week/this-month XP (from xp_events, timezone-
    aware, never cached/reset) plus lifetime XP (global_score)
    and accuracy (quiz_progress) for a single user - everything
    Profile needs, computed independently of each other.
    """

    period_row = db_execute(
        f"""
        SELECT
            COALESCE(SUM(xp) FILTER (
                WHERE created_at >= {_period_start_sql("day")}
            ), 0) AS today_xp,

            COALESCE(SUM(xp) FILTER (
                WHERE created_at >= {_period_start_sql("week")}
            ), 0) AS weekly_xp,

            COALESCE(SUM(xp) FILTER (
                WHERE created_at >= {_period_start_sql("month")}
            ), 0) AS monthly_xp

        FROM xp_events
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )

    overall_row = db_execute(
        """
        SELECT global_score
        FROM user_scores
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )

    return {
        "today_xp": period_row["today_xp"] if period_row else 0,
        "weekly_xp": period_row["weekly_xp"] if period_row else 0,
        "monthly_xp": period_row["monthly_xp"] if period_row else 0,
        "overall_xp": (
            overall_row["global_score"] if overall_row else 0
        ),
        "accuracy": get_accuracy(user_id),
    }