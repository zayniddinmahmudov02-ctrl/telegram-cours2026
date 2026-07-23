from .connection import db_execute


# =========================================================
# CREATE PAYMENT
# =========================================================

def create_payment(
    user_id: int,
    course: str,
    amount: int,
    receipt_file_id: str,
):
    db_execute(
        """
        INSERT INTO payments
        (
            user_id,
            course,
            amount,
            receipt_file_id,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            'pending'
        )
        """,
        (
            user_id,
            course,
            amount,
            receipt_file_id,
        ),
    )


# =========================================================
# GET PAYMENT
# =========================================================

def get_payment(payment_id: int):
    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE id=%s
        """,
        (payment_id,),
        fetchone=True,
    )


def get_user_payments(user_id: int):
    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


def get_pending_payments():
    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE status='pending'
        ORDER BY created_at
        """,
        fetchall=True,
    )


def get_buyers():
    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE status='approved'
        ORDER BY created_at DESC
        """,
        fetchall=True,
    )


# =========================================================
# STATUS
# =========================================================

def approve_payment(payment_id: int):
    db_execute(
        """
        UPDATE payments
        SET
            status='approved',
            approved_at=NOW()
        WHERE id=%s
        """,
        (payment_id,),
    )


def reject_payment(payment_id: int):
    db_execute(
        """
        UPDATE payments
        SET
            status='rejected'
        WHERE id=%s
        """,
        (payment_id,),
    )


# =========================================================
# EXISTS
# =========================================================

def payment_exists(user_id: int, course: str):
    row = db_execute(
        """
        SELECT id
        FROM payments
        WHERE
            user_id=%s
        AND
            course=%s
        AND
            status='approved'
        """,
        (
            user_id,
            course,
        ),
        fetchone=True,
    )

    return row is not None


# =========================================================
# DELETE
# =========================================================

def delete_payment(payment_id: int):
    db_execute(
        """
        DELETE
        FROM payments
        WHERE id=%s
        """,
        (payment_id,),
    )


# =========================================================
# STATISTICS
# =========================================================

def payments_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM payments
        """,
        fetchone=True,
    )

    return row[0]


def buyers_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM payments
        WHERE status='approved'
        """,
        fetchone=True,
    )

    return row[0]


def pending_count():
    row = db_execute(
        """
        SELECT COUNT(*)
        FROM payments
        WHERE status='pending'
        """,
        fetchone=True,
    )

    return row[0]