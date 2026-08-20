from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# CATEGORY LIST (root)
# =========================================================

def homework_categories_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"hw:cat:{category['id']}",
            )
        ]
        for category in categories
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data="hw:back_main",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def homework_password_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="hw:root",
                )
            ]
        ]
    )


# =========================================================
# CATEGORY HOME MENU
# =========================================================

def homework_menu_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Vazifa yuborish",
                    callback_data=f"hw:submit:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Qabul qilingan vazifalar",
                    callback_data=f"hw:history:{category_id}:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Umumiy ball",
                    callback_data=f"hw:total:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Profil",
                    callback_data=f"hw:profile:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="hw:root",
                )
            ],
        ]
    )


def homework_back_to_menu_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data=f"hw:menu:{category_id}",
                )
            ]
        ]
    )


# =========================================================
# SUBMISSION UPLOAD
# =========================================================

def homework_upload_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Vazifa yuborish",
                    callback_data=f"hw:finish:{submission_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"hw:cancel:{submission_id}",
                )
            ],
        ]
    )


def homework_confirm_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"hw:confirm:{submission_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Ortga qaytish",
                    callback_data=f"hw:continue:{submission_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"hw:cancel:{submission_id}",
                ),
            ],
        ]
    )


# =========================================================
# HISTORY PAGINATION
# =========================================================

def homework_history_keyboard(
    category_id: int,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:

    rows = []

    if total_pages > 1:
        nav_row = []

        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"hw:history:{category_id}:{page - 1}",
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="hw:noop",
            )
        )

        if page + 1 < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"hw:history:{category_id}:{page + 1}",
                )
            )

        rows.append(nav_row)

    rows.append(
        [
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=f"hw:menu:{category_id}",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


# =========================================================
# PROFILE
# =========================================================

def homework_profile_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Profilni tahrirlash",
                    callback_data=f"hw:profile:edit:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data=f"hw:menu:{category_id}",
                )
            ],
        ]
    )
