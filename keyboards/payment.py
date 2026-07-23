from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

# =========================================================
# COURSE KEYBOARD
# =========================================================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import COURSE_PRICES


def course_keyboard():
    keyboard = []

    for course, price in COURSE_PRICES.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{course} • {price:,} so'm",
                    callback_data=f"course:{course}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="payment_cancel",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )
# =========================================================
# PAYMENT MENU
# =========================================================

payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="💳 To'lov qilish"),
        ],
        [
            KeyboardButton(text="⬅️ Orqaga"),
        ],
    ],
    resize_keyboard=True,
)


# =========================================================
# CONTACT
# =========================================================

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 Telefon raqamni yuborish",
                request_contact=True,
            )
        ],
        [
            KeyboardButton(text="❌ Bekor qilish"),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# =========================================================
# CONFIRM
# =========================================================

confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data="payment_confirm",
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Qayta kiritish",
                callback_data="payment_restart",
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="payment_cancel",
            )
        ],
    ]
)


# =========================================================
# ADMIN
# =========================================================

def admin_payment_keyboard(payment_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve_payment:{payment_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject_payment:{payment_id}",
                ),
            ],
        ]
    )
