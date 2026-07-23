import uuid

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
):
    certificate_id = str(uuid.uuid4()).split("-")[0].upper()

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

        ON CONFLICT (user_id, certificate_type, level)

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

def get_certificate(certificate_id: str):
    return db_execute(
        """
        SELECT *
        FROM certificates
        WHERE certificate_id=%s
        """,
        (certificate_id,),
        fetchone=True,
    )


def get_user_certificates(user_id: int):
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
):
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

def delete_certificate(certificate_id: str):
    db_execute(
        """
        DELETE
        FROM certificates
        WHERE certificate_id=%s
        """,
        (certificate_id,),
    )


# =========================================================
# RANK
# =========================================================

def calculate_rank(percent: float):

    if percent >= 90:
        return "Gold"

    if percent >= 80:
        return "Silver"

    if percent >= 70:
        return "Bronze"

    return "Participant"


# =========================================================
# VERIFY
# =========================================================

def verify_certificate(certificate_id: str):
    return get_certificate(certificate_id) is not None


# =========================================================
# STATISTICS
# =========================================================

def certificates_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM certificates
        """,
        fetchone=True,
    )

    return row[0]


def level_certificates(level: str):
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