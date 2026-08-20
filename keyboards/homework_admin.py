from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# =========================================================
# SCORING (attached to the channel post, and reused in the
# Admin Panel's submission detail view for re-evaluation)
# =========================================================

def homework_score_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=str(score),
                    callback_data=f"hw:eval:{submission_id}:{score}",
                )
                for score in range(1, 6)
            ]
        ]
    )


# =========================================================
# ADMIN - CATEGORIES
# =========================================================

def homework_admin_categories_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:

    rows = []

    for category in categories:
        status = "🟢" if category["is_active"] else "🔴"

        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {category['name']}",
                    callback_data=f"hwa:cat:open:{category['id']}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="hwa:home",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def homework_admin_category_detail_keyboard(category: dict) -> InlineKeyboardMarkup:

    toggle_text = (
        "🔴 Faolsizlantirish"
        if category["is_active"]
        else "🟢 Faollashtirish"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=toggle_text,
                    callback_data=f"hwa:cat:toggle:{category['id']}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔑 Parolni o'zgartirish",
                    callback_data=f"hwa:cat:pwd:{category['id']}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="hwa:cat",
                )
            ],
        ]
    )


# =========================================================
# ADMIN - HOME
# =========================================================

def homework_admin_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📂 Kategoriyalar",
                    callback_data="hwa:cat",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Foydalanuvchilar",
                    callback_data="hwa:users:0:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Vazifalar",
                    callback_data="hwa:subs:0:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Statistika",
                    callback_data="hwa:stats",
                )
            ],
        ]
    )


# =========================================================
# ADMIN - PAGINATION (shared shape for users / submissions)
# =========================================================

def _admin_pagination_row(prefix: str, category_id: int, page: int, has_next: bool):
    row = []

    if page > 0:
        row.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"{prefix}:{category_id}:{page - 1}",
            )
        )

    row.append(
        InlineKeyboardButton(text=f"{page + 1}", callback_data="hw:noop")
    )

    if has_next:
        row.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"{prefix}:{category_id}:{page + 1}",
            )
        )

    return row


def homework_admin_users_keyboard(
    category_id: int,
    page: int,
    has_next: bool,
) -> InlineKeyboardMarkup:

    rows = [_admin_pagination_row("hwa:users", category_id, page, has_next)]

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="hwa:home",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def homework_admin_submissions_keyboard(
    submissions: list[dict],
    category_id: int,
    page: int,
    has_next: bool,
) -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                text=f"#{s['submission_uid']} - {s['first_name']} ({s['status']})"[:64],
                callback_data=f"hwa:subs:open:{s['id']}",
            )
        ]
        for s in submissions
    ]

    rows.append(_admin_pagination_row("hwa:subs", category_id, page, has_next))

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="hwa:home",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def homework_admin_submission_detail_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    keyboard = homework_score_keyboard(submission_id)

    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="hwa:subs:0:0",
            )
        ]
    )

    return keyboard
