from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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