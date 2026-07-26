import uuid

from config import (
    LEVEL_CONFIG,
    LEVEL_ORDER,
)

from .connection import db_execute


# =========================================================
# CREATE
# =========================================================

def create_certificate(
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

    db_execute(
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

def get_certificate(
    certificate_id: str,
):

    return db_execute(
        """
        SELECT *
        FROM certificates
        WHERE certificate_id=%s
        """,
        (certificate_id,),
        fetchone=True,
    )


def get_user_certificates(
    user_id: int,
):

    return db_execute(
        """
        SELECT *
        FROM certificates

        WHERE user_id=%s

        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


def get_level_certificate(
    user_id: int,
    certificate_type: str,
    level: str,
):

    return db_execute(
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

def certificate_exists(
    user_id: int,
    certificate_type: str,
    level: str,
) -> bool:

    row = db_execute(
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

def delete_certificate(
    certificate_id: str,
):

    db_execute(
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

def verify_certificate(
    certificate_id: str,
) -> bool:

    return (
        get_certificate(
            certificate_id
        )
        is not None
    )


# =========================================================
# STATISTICS
# =========================================================

def certificates_count() -> int:

    row = db_execute(
        """
        SELECT COUNT(*)

        FROM certificates
        """,
        fetchone=True,
    )

    return row[0]


def level_certificates(
    level: str,
) -> int:

    row = db_execute(
        """
        SELECT COUNT(*)

        FROM certificates

        WHERE level=%s
        """,
        (level,),
        fetchone=True,
    )

    return row[0]


# =========================================================
# QUIZ PROGRESS
# =========================================================

def get_block_score(
    user_id: int,
    level: str,
    block: int,
):

    return db_execute(
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


def get_level_progress(
    user_id: int,
    level: str,
) -> list[int]:

    config = LEVEL_CONFIG[level]

    scores = []

    for block in range(
        1,
        config["blocks"] + 1,
    ):

        row = get_block_score(
            user_id,
            level,
            block,
        )

        scores.append(
            row["best_score"]
            if row
            else 0
        )

    return scores


def get_all_progress(
    user_id: int,
) -> dict:

    return {
        level: get_level_progress(
            user_id,
            level,
        )
        for level in LEVEL_ORDER
    }