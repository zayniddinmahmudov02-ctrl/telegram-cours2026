from .connection import db_execute

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
    Add points to all active leaderboards.
    """

    create_user_score(user_id)

    db_execute(
        """
        UPDATE user_scores
        SET
            daily_score = daily_score + %s,
            weekly_score = weekly_score + %s,
            monthly_score = monthly_score + %s,
            global_score = global_score + %s,

            correct_answers = correct_answers + 1,

            updated_at = NOW()

        WHERE user_id = %s
        """,
        (
            points,
            points,
            points,
            points,
            user_id,
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

def get_top(period: str, limit: int = 100):

    columns = {
        "daily": "daily_score",
        "weekly": "weekly_score",
        "monthly": "monthly_score",
        "global": "global_score",
    }

    column = columns.get(period)

    if not column:
        return []

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


# =========================================================
# USER RANK
# =========================================================

def get_user_rank(user_id: int, period: str):

    columns = {
        "daily": "daily_score",
        "weekly": "weekly_score",
        "monthly": "monthly_score",
        "global": "global_score",
    }

    column = columns.get(period)

    if not column:
        return None

    row = db_execute(
        f"""
        SELECT rank
        FROM
        (
            SELECT
                user_id,
                RANK() OVER(
                    ORDER BY {column} DESC
                ) AS rank
            FROM user_scores
        ) ranks
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )

    return row["rank"] if row else None
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
# RESET
# =========================================================

def reset_daily():
    db_execute(
        """
        UPDATE user_scores
        SET
            daily_score = 0,
            updated_at = NOW()
        """
    )


def reset_weekly():
    db_execute(
        """
        UPDATE user_scores
        SET
            weekly_score = 0,
            updated_at = NOW()
        """
    )


def reset_monthly():
    db_execute(
        """
        UPDATE user_scores
        SET
            monthly_score = 0,
            updated_at = NOW()
        """
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

    row = db_execute(
        """
        SELECT
            correct_answers,
            wrong_answers
        FROM user_scores
        WHERE user_id = %s
        """,
        (user_id,),
        fetchone=True,
    )

    if not row:
        return 0

    correct = row["correct_answers"]
    wrong = row["wrong_answers"]

    total = correct + wrong

    if total == 0:
        return 0

    return round((correct / total) * 100, 1)