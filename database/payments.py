from .connection import db_execute
from .connection import db_execute

# =========================================================
# CREATE PAYMENT
# =========================================================

def create_payment(
    user_id: int,
    full_name: str,
    phone: str,
    username: str,
    course: str,
    amount: int,
    receipt_file_id: str,
    file_type: str,
):
    row = db_execute(
        """
        INSERT INTO payments
        (
            user_id,
            full_name,
            phone,
            username,
            course,
            amount,
            receipt_file_id,
            file_type,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            'pending'
        )
        RETURNING id;
        """,
        (
            user_id,
            full_name,
            phone,
            username,
            course,
            amount,
            receipt_file_id,
            file_type,
        ),
        fetchone=True,
    )

    return row[0] if row else None
# =========================================================
# GET
# =========================================================

def get_payment(payment_id: int):
    """
    Bitta paymentni ID bo'yicha olish.
    """

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
    """
    Foydalanuvchining barcha to'lovlari.
    """

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


def get_latest_payment(user_id: int):
    """
    Foydalanuvchining oxirgi paymenti.
    """

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,),
        fetchone=True,
    )


def get_pending_payments():
    """
    Tasdiqlanmagan paymentlar.
    """

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE status='pending'
        ORDER BY created_at ASC
        """,
        fetchall=True,
    )


def get_approved_payments():
    """
    Tasdiqlangan paymentlar.
    """

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE status='approved'
        ORDER BY approved_at DESC NULLS LAST
        """,
        fetchall=True,
    )


def get_rejected_payments():
    """
    Rad etilgan paymentlar.
    """

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE status='rejected'
        ORDER BY created_at DESC
        """,
        fetchall=True,
    )
# =========================================================
# SEARCH
# =========================================================

def search_payments(keyword: str):
    """
    Ism, username yoki Telegram ID bo'yicha qidiruv.
    """

    keyword = keyword.strip()

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE
            LOWER(full_name) LIKE LOWER(%s)
            OR LOWER(username) LIKE LOWER(%s)
            OR CAST(user_id AS TEXT) LIKE %s
        ORDER BY created_at DESC
        """,
        (
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%",
        ),
        fetchall=True,
    )


def search_by_phone(phone: str):
    """
    Telefon raqami bo'yicha qidiruv.
    """

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE phone=%s
        ORDER BY created_at DESC
        """,
        (phone,),
        fetchall=True,
    )


def get_customer_history(user_id: int):
    """
    Foydalanuvchining barcha xaridlari.
    """

    return db_execute(
        """
        SELECT
            course,
            amount,
            status,
            created_at
        FROM payments
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


def get_course_buyers(course: str):
    """
    Ma'lum kursni sotib olgan foydalanuvchilar.
    """

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE
            course=%s
            AND status='approved'
        ORDER BY created_at DESC
        """,
        (course,),
        fetchall=True,
    )
# =========================================================
# STATUS
# =========================================================

def approve_payment(payment_id: int, admin_id: int):
    """
    Paymentni tasdiqlash.
    """

    db_execute(
        """
        UPDATE payments
        SET
            status='approved',
            approved_by=%s,
            approved_at=NOW()
        WHERE id=%s
        """,
        (
            admin_id,
            payment_id,
        ),
    )


def reject_payment(payment_id: int, admin_id: int):
    """
    Paymentni rad etish.
    """

    db_execute(
        """
        UPDATE payments
        SET
            status='rejected',
            rejected_by=%s,
            rejected_at=NOW()
        WHERE id=%s
        """,
        (
            admin_id,
            payment_id,
        ),
    )


def cancel_payment(payment_id: int):
    """
    Paymentni bekor qilish.
    """

    db_execute(
        """
        UPDATE payments
        SET
            status='cancelled'
        WHERE id=%s
        """,
        (payment_id,),
    )


def refund_payment(payment_id: int):
    """
    Paymentni qaytarilgan deb belgilash.
    """

    db_execute(
        """
        UPDATE payments
        SET
            status='refunded'
        WHERE id=%s
        """,
        (payment_id,),
    )


def update_receipt(
    payment_id: int,
    receipt_file_id: str,
    file_type: str,
):
    """
    Chekni yangilash.
    """

    db_execute(
        """
        UPDATE payments
        SET
            receipt_file_id=%s,
            file_type=%s
        WHERE id=%s
        """,
        (
            receipt_file_id,
            file_type,
            payment_id,
        ),
    )
# =========================================================
# EXISTS
# =========================================================

def payment_exists(payment_id: int):
    """
    Payment mavjudligini tekshirish.
    """

    row = db_execute(
        """
        SELECT id
        FROM payments
        WHERE id=%s
        """,
        (payment_id,),
        fetchone=True,
    )

    return row is not None


def user_has_course(user_id: int, course: str):
    """
    Foydalanuvchi kursni sotib olganmi?
    """

    row = db_execute(
        """
        SELECT id
        FROM payments
        WHERE
            user_id=%s
            AND course=%s
            AND status='approved'
        LIMIT 1
        """,
        (
            user_id,
            course,
        ),
        fetchone=True,
    )

    return row is not None


def has_pending_payment(user_id: int):
    """
    Foydalanuvchida tasdiqlanmagan payment bormi?
    """

    row = db_execute(
        """
        SELECT id
        FROM payments
        WHERE
            user_id=%s
            AND status='pending'
        LIMIT 1
        """,
        (user_id,),
        fetchone=True,
    )

    return row is not None


def has_rejected_payment(user_id: int):
    """
    Foydalanuvchida rad etilgan payment bormi?
    """

    row = db_execute(
        """
        SELECT id
        FROM payments
        WHERE
            user_id=%s
            AND status='rejected'
        LIMIT 1
        """,
        (user_id,),
        fetchone=True,
    )

    return row is not None
# =========================================================
# DELETE
# =========================================================

def delete_payment(payment_id: int):
    """
    Paymentni soft delete qilish.
    """

    db_execute(
        """
        UPDATE payments
        SET
            is_deleted=TRUE
        WHERE id=%s
        """,
        (payment_id,),
    )


def restore_payment(payment_id: int):
    """
    O'chirilgan paymentni tiklash.
    """

    db_execute(
        """
        UPDATE payments
        SET
            is_deleted=FALSE
        WHERE id=%s
        """,
        (payment_id,),
    )


def get_deleted_payments():
    """
    O'chirilgan paymentlar.
    """

    return db_execute(
        """
        SELECT *
        FROM payments
        WHERE is_deleted=TRUE
        ORDER BY created_at DESC
        """,
        fetchall=True,
    )
# =========================================================
# STATISTICS
# =========================================================

def get_payment_statistics():
    """
    Payment statistikasi.
    """

    row = db_execute(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE is_deleted = FALSE
            ) AS total_payments,

            COUNT(*) FILTER (
                WHERE status = 'approved'
                AND is_deleted = FALSE
            ) AS approved,

            COUNT(*) FILTER (
                WHERE status = 'pending'
                AND is_deleted = FALSE
            ) AS pending,

            COUNT(*) FILTER (
                WHERE status = 'rejected'
                AND is_deleted = FALSE
            ) AS rejected,

            COUNT(*) FILTER (
                WHERE status = 'cancelled'
                AND is_deleted = FALSE
            ) AS cancelled,

            COUNT(*) FILTER (
                WHERE status = 'refunded'
                AND is_deleted = FALSE
            ) AS refunded,

            COALESCE(
                SUM(amount) FILTER (
                    WHERE status = 'approved'
                    AND is_deleted = FALSE
                ),
                0
            ) AS total_income,

            COALESCE(
                SUM(amount) FILTER (
                    WHERE status = 'approved'
                    AND approved_at::date = CURRENT_DATE
                    AND is_deleted = FALSE
                ),
                0
            ) AS today_income,

            COALESCE(
                SUM(amount) FILTER (
                    WHERE status = 'approved'
                    AND approved_at >= NOW() - INTERVAL '30 days'
                    AND is_deleted = FALSE
                ),
                0
            ) AS monthly_income

        FROM payments
        """,
        fetchone=True,
    )

    return {
        "total_payments": row[0],
        "approved": row[1],
        "pending": row[2],
        "rejected": row[3],
        "cancelled": row[4],
        "refunded": row[5],
        "total_income": row[6],
        "today_income": row[7],
        "monthly_income": row[8],
    }
# =========================================================
# APPROVED PAYMENTS
# =========================================================

def get_approved_payments():

    return db_execute(
        """
        SELECT
            id,
            user_id,
            full_name,
            phone,
            username,
            course,
            amount,
            approved_at
        FROM payments
        WHERE status='approved'
        AND is_deleted=FALSE
        ORDER BY approved_at DESC
        """,
        fetchall=True,
    )
# =========================================================
# RECENT PAYMENTS
# =========================================================

def get_recent_payments(limit=30):

    return db_execute(
        """
        SELECT
            id,
            full_name,
            course,
            amount,
            status,
            created_at
        FROM payments
        WHERE is_deleted = FALSE
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
        fetchall=True,
    )