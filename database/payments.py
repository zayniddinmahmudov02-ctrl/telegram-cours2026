from .connection import db_execute

# =========================================================
# CREATE PAYMENT
# =========================================================

async def create_payment(
    user_id: int,
    full_name: str,
    phone: str,
    username: str,
    course: str,
    amount: int,
    receipt_file_id: str,
    file_type: str,
):
    row = await db_execute(
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

    if not row:
        return None

    return row["id"]

# =========================================================
# SAVE CHANNEL MESSAGE
# =========================================================

async def save_channel_message(
    payment_id: int,
    channel_id: int,
    message_id: int,
):
    await db_execute(
        """
        UPDATE payments
        SET
            channel_id=%s,
            channel_message_id=%s
        WHERE id=%s
        """,
        (
            channel_id,
            message_id,
            payment_id,
        ),
    )
# =========================================================
# GET
# =========================================================

async def get_payment(payment_id: int):
    """
    Bitta paymentni ID bo'yicha olish.
    """

    return await db_execute(
        """
        SELECT *
        FROM payments
        WHERE id=%s
        """,
        (payment_id,),
        fetchone=True,
    )


async def get_user_payments(user_id: int):
    """
    Foydalanuvchining barcha to'lovlari.
    """

    return await db_execute(
        """
        SELECT *
        FROM payments
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetchall=True,
    )


async def get_latest_payment(user_id: int):
    """
    Foydalanuvchining oxirgi paymenti.
    """

    return await db_execute(
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


async def get_pending_payments():
    """
    Tasdiqlanmagan paymentlar.
    """

    return await db_execute(
        """
        SELECT *
        FROM payments
        WHERE status='pending'
        ORDER BY created_at ASC
        """,
        fetchall=True,
    )


async def get_rejected_payments():
    """
    Rad etilgan paymentlar.
    """

    return await db_execute(
        """
        SELECT *
        FROM payments
        WHERE status='rejected'
        ORDER BY created_at DESC
        """,
        fetchall=True,
    )
# NOTE: get_approved_payments() is defined once below (near
# APPROVED PAYMENTS), which is the version actually in effect -
# an earlier duplicate definition here (dead code, unreachable
# since Python keeps only the last def) was removed.
# =========================================================
# SEARCH
# =========================================================

async def search_payments(keyword: str):
    """
    Ism, username yoki Telegram ID bo'yicha qidiruv.
    """

    keyword = keyword.strip()

    return await db_execute(
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


async def search_by_phone(phone: str):
    """
    Telefon raqami bo'yicha qidiruv.
    """

    return await db_execute(
        """
        SELECT *
        FROM payments
        WHERE phone=%s
        ORDER BY created_at DESC
        """,
        (phone,),
        fetchall=True,
    )


async def get_customer_history(user_id: int):
    """
    Foydalanuvchining barcha xaridlari.
    """

    return await db_execute(
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


async def get_course_buyers(course: str):
    """
    Ma'lum kursni sotib olgan foydalanuvchilar.
    """

    return await db_execute(
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

async def approve_payment(payment_id: int, admin_id: int):
    """
    Paymentni tasdiqlash.
    """

    await db_execute(
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


async def reject_payment(payment_id: int, admin_id: int):
    """
    Paymentni rad etish.
    """

    await db_execute(
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


async def cancel_payment(payment_id: int):
    """
    Paymentni bekor qilish.
    """

    await db_execute(
        """
        UPDATE payments
        SET
            status='cancelled'
        WHERE id=%s
        """,
        (payment_id,),
    )


async def refund_payment(payment_id: int):
    """
    Paymentni qaytarilgan deb belgilash.
    """

    await db_execute(
        """
        UPDATE payments
        SET
            status='refunded'
        WHERE id=%s
        """,
        (payment_id,),
    )


async def update_receipt(
    payment_id: int,
    receipt_file_id: str,
    file_type: str,
):
    """
    Chekni yangilash.
    """

    await db_execute(
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

async def payment_exists(payment_id: int):
    """
    Payment mavjudligini tekshirish.
    """

    row = await db_execute(
        """
        SELECT id
        FROM payments
        WHERE id=%s
        """,
        (payment_id,),
        fetchone=True,
    )

    return row is not None


async def user_has_course(user_id: int, course: str):
    """
    Foydalanuvchi kursni sotib olganmi?
    """

    row = await db_execute(
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


async def has_pending_payment(user_id: int):
    """
    Foydalanuvchida tasdiqlanmagan payment bormi?
    """

    row = await db_execute(
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


async def has_rejected_payment(user_id: int):
    """
    Foydalanuvchida rad etilgan payment bormi?
    """

    row = await db_execute(
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

async def delete_payment(payment_id: int):
    """
    Paymentni soft delete qilish.
    """

    await db_execute(
        """
        UPDATE payments
        SET
            is_deleted=TRUE
        WHERE id=%s
        """,
        (payment_id,),
    )


async def restore_payment(payment_id: int):
    """
    O'chirilgan paymentni tiklash.
    """

    await db_execute(
        """
        UPDATE payments
        SET
            is_deleted=FALSE
        WHERE id=%s
        """,
        (payment_id,),
    )


async def get_deleted_payments():
    """
    O'chirilgan paymentlar.
    """

    return await db_execute(
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

async def get_payment_statistics():
    """
    Payment statistikasi.
    """

    row = await db_execute(
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
        "total_payments": row["total_payments"],
        "approved": row["approved"],
        "pending": row["pending"],
        "rejected": row["rejected"],
        "cancelled": row["cancelled"],
        "refunded": row["refunded"],
        "total_income": row["total_income"],
        "today_income": row["today_income"],
        "monthly_income": row["monthly_income"],
    }


async def get_distinct_buyers_count():
    """
    Kamida bitta tasdiqlangan to'lovi bor
    noyob foydalanuvchilar soni.
    """

    row = await db_execute(
        """
        SELECT COUNT(DISTINCT user_id) AS count
        FROM payments
        WHERE status='approved'
        """,
        fetchone=True,
    )

    return row["count"]
# =========================================================
# APPROVED PAYMENTS
# =========================================================

async def get_approved_payments():

    return await db_execute(
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

async def get_recent_payments(limit=30):

    return await db_execute(
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
