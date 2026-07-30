from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config import LEVEL_ORDER

# =========================================================
# MY CERTIFICATES (PROFILE)
# =========================================================

def certificates_keyboard(
    certificates: list[dict],
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📄 {c['level']} PDF",
                    callback_data=f"profile_cert:{c['level']}",
                )
            ]
            for c in certificates
        ]
    )


# =========================================================
# ADMIN CERTIFICATES MENU
# =========================================================

def admin_certificates_keyboard() -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                text=f"🧪 {level} (test)",
                callback_data=f"admin_cert:generate:{level}",
            )
        ]
        for level in LEVEL_ORDER
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text="📂 Sertifikatlarni ko'rish",
                callback_data="admin_cert:browse",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


# =========================================================
# ADMIN CERTIFICATES BROWSE
# =========================================================

def admin_certificates_browse_keyboard(
    certificates: list[dict],
) -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                text=(
                    f"📄 {c['level']} - "
                    f"{c['full_name']} ({c['rank']})"
                )[:64],
                callback_data=(
                    f"admin_cert:open:{c['certificate_id']}"
                ),
            )
        ]
        for c in certificates
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="admin_cert:home",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
