from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# PENDING HOMEWORKS
# =========================================================

def pending_homeworks_keyboard(
    submissions: list[dict],
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    if not submissions:
        builder.button(
            text="📭 Homework topilmadi",
            callback_data="teacher_hw_empty",
        )
    else:
        for submission in submissions:

            builder.button(
                text=(
                    f"{submission['level']} • "
                    f"{submission['lesson']} • "
                    f"#{submission['id']}"
                ),
                callback_data=(
                    f"teacher_hw:{submission['id']}"
                ),
            )

    builder.button(
        text="🔄 Yangilash",
        callback_data="teacher_hw_refresh",
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
        callback_data=f"teacher_hw_accept:{submission_id}",
    )

    builder.button(
        text="❌ Rad etish",
        callback_data=f"teacher_hw_reject:{submission_id}",
    )

    builder.button(
        text="💬 Izoh yozish",
        callback_data=f"teacher_hw_comment:{submission_id}",
    )

    builder.button(
        text="📥 Homeworklar",
        callback_data="teacher_hw_refresh",
    )

    builder.button(
        text="⬅️ Orqaga",
        callback_data="teacher_panel",
    )

    builder.adjust(2, 1, 1, 1)

    return builder.as_markup()