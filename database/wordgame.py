from .connection import db_execute

# =========================================================
# PROGRESS
# =========================================================

def get_progress(user_id, level, block):
    return db_execute(
        """
        SELECT *
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        AND block_number=%s
        """,
        (user_id, level, block),
        fetchone=True,
    )


def get_best_score(user_id, level, block):
    row = db_execute(
        """
        SELECT best_score
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        AND block_number=%s
        """,
        (user_id, level, block),
        fetchone=True,
    )

    return row[0] if row else 0


# =========================================================
# SAVE
# =========================================================

def save_progress(user_id, level, block, score):
    db_execute(
        """
        INSERT INTO quiz_progress
        (
            user_id,
            level,
            block_number,
            best_score
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )

        ON CONFLICT
        (
            user_id,
            level,
            block_number
        )

        DO UPDATE SET
        best_score=
        GREATEST(
            quiz_progress.best_score,
            EXCLUDED.best_score
        )
        """,
        (
            user_id,
            level,
            block,
            score,
        ),
    )


# =========================================================
# LEVEL SCORE
# =========================================================

def get_level_score(user_id, level):
    row = db_execute(
        """
        SELECT
        COALESCE(SUM(best_score),0)
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        """,
        (user_id, level),
        fetchone=True,
    )

    return row[0] if row else 0


def get_level_blocks(user_id, level):
    return db_execute(
        """
        SELECT
        block_number,
        best_score
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        ORDER BY block_number
        """,
        (user_id, level),
        fetchall=True,
    )


# =========================================================
# CHECKS
# =========================================================

def block_completed(user_id, level, block):
    score = get_best_score(user_id, level, block)
    return score >= 60


def previous_block_completed(user_id, level, block):
    if block == 1:
        return True

    score = get_best_score(user_id, level, block - 1)

    return score >= 60


def level_completed(user_id, level, blocks):
    for block in range(1, blocks + 1):

        if get_best_score(user_id, level, block) < 60:
            return False

    return True


# =========================================================
# XP
# =========================================================

def calculate_xp(old_score, new_score):

    if new_score <= old_score:
        return 0

    return new_score - old_score


# =========================================================
# LEVEL UNLOCK
# =========================================================

def unlock_level(user_id, level):
    db_execute(
        """
        UPDATE users
        SET unlocked_level=%s
        WHERE user_id=%s
        """,
        (
            level,
            user_id,
        ),
    )


# =========================================================
# STATS
# =========================================================

def total_questions(level):
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM quiz_progress
        WHERE level=%s
        """,
        (level,),
        fetchone=True,
    )

    return row[0]


def user_progress_percent(user_id, level, total_blocks):

    score = get_level_score(user_id, level)

    max_score = total_blocks * 100

    if max_score == 0:
        return 0

    return round(score / max_score * 100, 1)


# =========================================================
# RESET
# =========================================================

def clear_progress(user_id):

    db_execute(
        """
        DELETE
        FROM quiz_progress
        WHERE user_id=%s
        """,
        (user_id,),
    )


def clear_level_progress(user_id, level):

    db_execute(
        """
        DELETE
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        """,
        (
            user_id,
            level,
        ),
    )