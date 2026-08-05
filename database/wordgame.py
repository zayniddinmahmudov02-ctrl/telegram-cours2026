from .connection import db_execute

# =========================================================
# PROGRESS
# =========================================================

async def get_progress(user_id, level, block):
    return await db_execute(
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


async def get_best_score(user_id, level, block):
    row = await db_execute(
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

    return row["best_score"] if row else 0


# =========================================================
# SAVE
# =========================================================

async def save_progress(user_id, level, block, score):
    await db_execute(
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

async def get_level_score(user_id, level):
    row = await db_execute(
        """
        SELECT
        COALESCE(SUM(best_score),0) AS total
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        """,
        (user_id, level),
        fetchone=True,
    )

    return row["total"] if row else 0


async def get_level_blocks(user_id, level):
    return await db_execute(
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

async def block_completed(user_id, level, block):
    score = await get_best_score(user_id, level, block)
    return score >= 60


async def previous_block_completed(user_id, level, block):
    if block == 1:
        return True

    score = await get_best_score(user_id, level, block - 1)

    return score >= 60


async def level_completed(user_id, level, blocks):
    for block in range(1, blocks + 1):

        if await get_best_score(user_id, level, block) < 60:
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

async def unlock_level(user_id, level):
    await db_execute(
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

async def total_questions(level):
    row = await db_execute(
        """
        SELECT COUNT(*) AS count
        FROM quiz_progress
        WHERE level=%s
        """,
        (level,),
        fetchone=True,
    )

    return row["count"]


async def user_progress_percent(user_id, level, total_blocks):

    score = await get_level_score(user_id, level)

    max_score = total_blocks * 100

    if max_score == 0:
        return 0

    return round(score / max_score * 100, 1)


# =========================================================
# RESET
# =========================================================

async def clear_progress(user_id):

    await db_execute(
        """
        DELETE
        FROM quiz_progress
        WHERE user_id=%s
        """,
        (user_id,),
    )


async def clear_level_progress(user_id, level):

    await db_execute(
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
