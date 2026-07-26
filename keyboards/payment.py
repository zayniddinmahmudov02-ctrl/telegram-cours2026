from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# =========================================================
# PHONE KEYBOARD
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
            KeyboardButton(
                text="❌ Bekor qilish",
            )
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
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
            ]
        ]
    )