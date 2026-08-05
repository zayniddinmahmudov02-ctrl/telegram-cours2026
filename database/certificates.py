import asyncio
import uuid

from config import (
    LEVEL_CONFIG,
    LEVEL_ORDER,
)

from .connection import db_execute


# =========================================================
# CREATE
# =========================================================

async def create_certificate(
    user_id: int,
    certificate_type: str,
    level: str,
    score: int,
    percent: float,
    rank: str,
) -> str:

    certificate_id = (
        "VIZU-"
        + uuid.uuid4().hex[:12].upper()
    )

    await db_execute(
        """
        INSERT INTO certificates
        (
            certificate_id,
            user_id,
            certificate_type,
            level,
            score,
            percent,
            rank
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )

        ON CONFLICT
        (
            user_id,
            certificate_type,
            level
        )

        DO UPDATE SET

            score=EXCLUDED.score,
            percent=EXCLUDED.percent,
            rank=EXCLUDED.rank,
            created_at=NOW()
        """,
        (
            certificate_id,
            user_id,
            certificate_type,
            level,
            score,
            percent,
            rank,
        ),
    )

    return certificate_id


# =========================================================
# GET
# =========================================================

async def get_certificate(
    certificate_id: str,
):

    return await db_execute(
        """
        SELECT *
        FROM certificates
        WHERE certificate_id=%s
        """,
        (certificate_id,),
        fetchone=True,
    )


async def get_user_certificates(
    user_id: int,
):

    return await db_execute(
        """
        SELECT *
        FROM certificates

        WHERE user_id=%s

        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


async def get_level_certificate(
    user_id: int,
    certificate_type: str,
    level: str,
):

    return await db_execute(
        """
        SELECT *

        FROM certificates

        WHERE
            user_id=%s

        AND
            certificate_type=%s

        AND
            level=%s
        """,
        (
            user_id,
            certificate_type,
            level,
        ),
        fetchone=True,
    )


# =========================================================
# EXISTS
# =========================================================

async def certificate_exists(
    user_id: int,
    certificate_type: str,
    level: str,
) -> bool:

    row = await db_execute(
        """
        SELECT certificate_id

        FROM certificates

        WHERE
            user_id=%s

        AND
            certificate_type=%s

        AND
            level=%s
        """,
        (
            user_id,
            certificate_type,
            level,
        ),
        fetchone=True,
    )

    return row is not None
# =========================================================
# DELETE
# =========================================================

async def delete_certificate(
    certificate_id: str,
):

    await db_execute(
        """
        DELETE

        FROM certificates

        WHERE certificate_id=%s
        """,
        (certificate_id,),
    )


# =========================================================
# VERIFY
# =========================================================

async def verify_certificate(
    certificate_id: str,
) -> bool:

    return (
        await get_certificate(
            certificate_id
        )
        is not None
    )


# =========================================================
# STATISTICS
# =========================================================

async def certificates_count() -> int:

    row = await db_execute(
        """
        SELECT COUNT(*) AS count

        FROM certificates
        """,
        fetchone=True,
    )

    return row["count"]


async def wordgame_certificates_count() -> int:
    """So'z O'yini orqali berilgan sertifikatlar soni."""

    row = await db_execute(
        """
        SELECT COUNT(*) AS count

        FROM certificates

        WHERE certificate_type='W'
        """,
        fetchone=True,
    )

    return row["count"]


async def get_recent_certificates(limit: int = 20):
    """
    Most recently issued certificates, across all users, for
    the admin panel's "browse generated certificates" view.
    """

    return await db_execute(
        """
        SELECT
            c.certificate_id,
            c.user_id,
            c.level,
            c.rank,
            c.score,
            c.created_at,
            u.full_name
        FROM certificates c
        INNER JOIN users u
            ON u.user_id = c.user_id
        ORDER BY c.created_at DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )


async def level_certificates(
    level: str,
) -> int:

    row = await db_execute(
        """
        SELECT COUNT(*) AS count

        FROM certificates

        WHERE level=%s
        """,
        (level,),
        fetchone=True,
    )

    return row["count"]


# =========================================================
# QUIZ PROGRESS
# =========================================================

async def get_block_score(
    user_id: int,
    level: str,
    block: int,
):

    return await db_execute(
        """
        SELECT
            best_score

        FROM quiz_progress

        WHERE
            user_id=%s

        AND
            level=%s

        AND
            block_number=%s
        """,
        (
            user_id,
            level,
            block,
        ),
        fetchone=True,
    )


async def get_level_progress(
    user_id: int,
    level: str,
) -> list[int]:
    """
    Best score per block, 0 for blocks never attempted.

    Fetches the whole level's quiz_progress rows in a single
    query (instead of one SELECT per block - up to 15 round
    trips for B2) and fills in the gaps in memory.
    """

    config = LEVEL_CONFIG[level]

    rows = await db_execute(
        """
        SELECT
            block_number,
            best_score
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        """,
        (user_id, level),
        fetchall=True,
    )

    scores_by_block = {
        row["block_number"]: row["best_score"]
        for row in rows
    }

    return [
        scores_by_block.get(block, 0)
        for block in range(1, config["blocks"] + 1)
    ]


async def get_all_progress(
    user_id: int,
) -> dict:
    """
    Progress for every level. The 5 levels are independent
    reads, fetched concurrently rather than one after another.
    """

    results = await asyncio.gather(
        *(
            get_level_progress(user_id, level)
            for level in LEVEL_ORDER
        )
    )

    return dict(zip(LEVEL_ORDER, results))
