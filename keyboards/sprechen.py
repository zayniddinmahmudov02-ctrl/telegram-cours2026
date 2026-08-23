# =========================================================
# SPRECHEN GURUH - KEYBOARDS
# =========================================================
# Kept separate from keyboards/homework.py since Sprechen's menu
# shape (a 20-lesson grid + gender/level-group registration) is
# fundamentally different from the generic Submit/History/Score/
# Profile menu used by Video/Online - see handlers/homework/
# sprechen.py for why the flow itself branches this early too.

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from services.homework import GENDER_LABELS, LEVEL_GROUP_LABELS, SPRECHEN_LESSON_COUNT

# =========================================================
# REGISTRATION - GENDER / LEVEL GROUP
# =========================================================

def sprechen_gender_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"hw:sp:gender:{category_id}:{code}",
                )
            ]
            for code, label in GENDER_LABELS.items()
        ]
    )


def sprechen_level_group_keyboard(category_id: int, gender: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"hw:sp:level:{category_id}:{gender}:{code}",
                )
            ]
            for code, label in LEVEL_GROUP_LABELS.items()
        ]
    )


# =========================================================
# LESSON GRID
# =========================================================

def sprechen_lesson_grid_keyboard(
    category_id: int,
    completed_lessons: set[int],
) -> InlineKeyboardMarkup:

    rows = []
    row = []

    for n in range(1, SPRECHEN_LESSON_COUNT + 1):
        text = f"✅ {n}" if n in completed_lessons else f"📖 {n}"

        row.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"hw:sp:lesson:{category_id}:{n}",
            )
        )

        if len(row) == 4:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                text="🏆 Umumiy ball",
                callback_data=f"hw:sp:total:{category_id}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="⚙️ Profil",
                callback_data=f"hw:sp:profile:{category_id}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data="hw:root",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


# =========================================================
# SIMPLE "BACK TO LESSON GRID" SCREENS (Profile / Total score)
# =========================================================

def sprechen_back_to_menu_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data=f"hw:sp:menu:{category_id}",
                )
            ]
        ]
    )
