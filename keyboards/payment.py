from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from config.settings import COURSE_INFO


# =========================================================
# COURSE KEYBOARD
# =========================================================

def course_keyboard():

    keyboard = []

    for course, info in COURSE_INFO.items():

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{course} • {info['price']}",
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
        inline_keyboard=keyboard,
    )


# =========================================================
# PAYMENT MENU
# =========================================================

payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="💳 To'lov qilish",
            ),
        ],
        [
            KeyboardButton(
                text="⬅️ Orqaga",
            ),
        ],
    ],
    resize_keyboard=True,
)


# =========================================================
# CONTACT KEYBOARD
# =========================================================

phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 Telefon raqamni yuborish",
                request_contact=True,
            ),
        ],
        [
            KeyboardButton(
                text="❌ Bekor qilish",
            ),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


# =========================================================
# CONFIRM KEYBOARD
# =========================================================

confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data="payment_confirm",
            ),
        ],
        [
            InlineKeyboardButton(
                text="✏️ Qayta kiritish",
                callback_data="payment_restart",
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="payment_cancel",
            ),
        ],
    ]
)


# =========================================================
# ADMIN PAYMENT KEYBOARD
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
        ],
    )