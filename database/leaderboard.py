from .connection import db_execute

# =========================================================
# CREATE / UPDATE
# =========================================================

def create_user_score(user_id):
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


def add_score(user_id, points):
    create_user_score(user_id)

    db_execute(
        """
        UPDATE user_scores
        SET
            daily_score=daily_score+%s,
            weekly_score=weekly_score+%s,
            monthly_score=monthly_score+%s,
            global_score=global_score+%s,
            correct_answers=correct_answers+1,
            updated_at=NOW()
        WHERE user_id=%s
        """,
        (
            points,
            points,
            points,
            points,
            user_id,
        ),
    )


def add_wrong_answer(user_id):
    create_user_score(user_id)

    db_execute(
        """
        UPDATE user_scores
        SET
            wrong_answers=wrong_answers+1,
            updated_at=NOW()
        WHERE user_id=%s
        """,
        (
            user_id,
        ),
    )


# =========================================================
# GETTERS
# =========================================================

def get_user_score(user_id):
    return db_execute(
        """
        SELECT *
        FROM user_scores
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )


def get_daily_top(limit=100):
    return db_execute(
        """
        SELECT *
        FROM user_scores
        ORDER BY daily_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


def get_weekly_top(limit=100):
    return db_execute(
        """
        SELECT *
        FROM user_scores
        ORDER BY weekly_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


def get_monthly_top(limit=100):
    return db_execute(
        """
        SELECT *
        FROM user_scores
        ORDER BY monthly_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


def get_global_top(limit=100):
    return db_execute(
        """
        SELECT *
        FROM user_scores
        ORDER BY global_score DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )
# =========================================================
# RANKS
# =========================================================

def get_user_rank(user_id, period):

    if period not in (
        "daily",
        "weekly",
        "monthly",
        "global",
    ):
        return None

    column = f"{period}_score"

    row = db_execute(
        f"""
        SELECT rank
        FROM
        (
            SELECT
                user_id,
                RANK() OVER
                (
                    ORDER BY {column} DESC
                ) AS rank
            FROM user_scores
        ) t
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )

    return row[0] if row else None


# =========================================================
# CHAMPIONS
# =========================================================

def save_weekly_champion(
    year,
    week,
    user_id,
    full_name,
    score,
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
            year,
            week,
            user_id,
            full_name,
            score,
        ),
    )


def save_monthly_champion(
    year,
    month,
    user_id,
    full_name,
    score,
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
            year,
            month,
            user_id,
            full_name,
            score,
        ),
    )


def get_monthly_champions(year):
    return db_execute(
        """
        SELECT *
        FROM monthly_champions
        WHERE year=%s
        ORDER BY month
        """,
        (year,),
        fetchall=True,
    )


def get_weekly_champions(year):
    return db_execute(
        """
        SELECT *
        FROM weekly_champions
        WHERE year=%s
        ORDER BY week
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
            daily_score=0
        """
    )


def reset_weekly():
    db_execute(
        """
        UPDATE user_scores
        SET
            weekly_score=0
        """
    )


def reset_monthly():
    db_execute(
        """
        UPDATE user_scores
        SET
            monthly_score=0
        """
    )


# =========================================================
# HALL OF FAME
# =========================================================

def save_hall_of_fame(
    year,
    month,
    champion_id,
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


def get_hall_of_fame(year):
    return db_execute(
        """
        SELECT *
        FROM hall_of_fame
        WHERE year=%s
        ORDER BY month
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
        SELECT COUNT(*)
        FROM user_scores
        """,
        fetchone=True,
    )

    return row[0] if row else 0


def get_top_player(period):

    if period not in (
        "daily",
        "weekly",
        "monthly",
        "global",
    ):
        return None

    column = f"{period}_score"

    return db_execute(
        f"""
        SELECT *
        FROM user_scores
        ORDER BY {column} DESC
        LIMIT 1
        """,
        fetchone=True,
    )


def get_user_statistics(user_id):
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
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True,
    )