from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# LEVELS
# =========================================================

def homework_levels_keyboard(
    course_type: str,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    levels = [
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
    ]

    for level in levels:
        builder.button(
            text=level,
            callback_data=f"hw_{course_type}_level:{level}",
        )

    builder.adjust(2, 2, 1)

    builder.button(
        text="⬅️ Orqaga",
        callback_data=f"hw_{course_type}_back",
    )

    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


# =========================================================
# LESSONS
# =========================================================

def homework_lessons_keyboard(
    course_type: str,
    level: str,
    total_lessons: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    for lesson in range(1, total_lessons + 1):

        builder.button(
            text=str(lesson),
            callback_data=(
                f"hw_{course_type}_lesson:"
                f"{level}:{lesson}"
            ),
        )

    builder.adjust(5)

    builder.button(
        text="⬅️ Orqaga",
        callback_data=f"hw_{course_type}_back",
    )

    builder.adjust(5, 1)

    return builder.as_markup()
# =========================================================
# COMPONENTS
# =========================================================

def homework_components_keyboard(
    course_type: str,
    level: str,
    lesson: int,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    components = [
        ("📖 Grammatik", "grammar"),
        ("📚 Lesen", "reading"),
        ("🎧 Hören", "listening"),
        ("✍️ Schreiben", "writing"),
        ("🗣 Sprechen", "speaking"),
        ("📖 Wortschatz", "vocabulary"),
    ]

    for text, component in components:
        builder.button(
            text=text,
            callback_data=(
                f"hw_{course_type}_component:"
                f"{level}:{lesson}:{component}"
            ),
        )

    builder.adjust(2, 2, 2)

    builder.button(
        text="⬅️ Orqaga",
        callback_data=(
            f"hw_{course_type}_level:{level}"
        ),
    )

    builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


# =========================================================
# SUBMIT HOMEWORK
# =========================================================

def homework_submit_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📤 Vazifalarni yuborish",
        callback_data="hw_submit",
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data="hw_cancel",
    )

    builder.adjust(1, 1)

    return builder.as_markup()


# =========================================================
# SPEAKING TASK
# =========================================================

def speaking_task_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Keyingi Task",
        callback_data="hw_speaking_next",
    )

    builder.button(
        text="📤 Darsni yakunlash",
        callback_data="hw_speaking_finish",
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data="hw_speaking_cancel",
    )

    builder.adjust(1, 1, 1)

    return builder.as_markup()
# =========================================================
# TEACHER HOMEWORK LIST
# =========================================================

def pending_homeworks_keyboard(
    submissions: list[dict],
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

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

    builder.adjust(1)

    builder.button(
        text="🔄 Yangilash",
        callback_data="teacher_hw_refresh",
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# TEACHER ACTIONS
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
        text="⬅️ Orqaga",
        callback_data="teacher_hw_back",
    )

    builder.adjust(2, 1, 1)

    return builder.as_markup()


# =========================================================
# UNIVERSAL SUBMIT BUTTON
# =========================================================

def homework_submit_keyboard(
    course_type: str,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📤 Vazifalarni yuborish",
        callback_data=f"hw_{course_type}_submit",
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data=f"hw_{course_type}_cancel",
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# SPEAKING TASK BUTTONS
# =========================================================

def speaking_task_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Keyingi Task",
        callback_data="hw_speaking_next",
    )

    builder.button(
        text="📤 Darsni yakunlash",
        callback_data="hw_speaking_finish",
    )

    builder.button(
        text="❌ Bekor qilish",
        callback_data="hw_speaking_cancel",
    )

    builder.adjust(1)

    return builder.as_markup()
# =========================================================
# TEACHER CHAT
# =========================================================

def teacher_chat_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="❌ Suhbatni yakunlash",
        callback_data="teacher_chat_close",
    )

    builder.adjust(1)

    return builder.as_markup()