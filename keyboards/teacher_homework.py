from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# PENDING HOMEWORKS
# =========================================================

def pending_homeworks_keyboard(
    submissions: list,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    for submission in submissions:

        builder.button(
            text=(
                f"{submission['level']} • "
                f"{submission['lesson']} • "
                f"{submission['user_id']}"
            ),
            callback_data=(
                f"teacher_submission:{submission['id']}"
            ),
        )

    builder.button(
        text="🔄 Yangilash",
        callback_data="teacher_homeworks_refresh",
    )

    builder.button(
        text="⬅️ Orqaga",
        callback_data="teacher_panel",
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# SUBMISSION ACTIONS
# =========================================================

def submission_actions_keyboard(
    submission_id: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Tasdiqlash",
        callback_data=f"teacher_approve:{submission_id}",
    )

    builder.button(
        text="❌ Rad etish",
        callback_data=f"teacher_reject:{submission_id}",
    )

    builder.button(
        text="📥 Homeworklar",
        callback_data="teacher_homeworks_refresh",
    )

    builder.adjust(2, 1)

    return builder.as_markup()