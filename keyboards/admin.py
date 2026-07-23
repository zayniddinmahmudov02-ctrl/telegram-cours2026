admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="👥 Foydalanuvchilar"),
        ],
        [
            KeyboardButton(text="💳 Xaridorlar"),
            KeyboardButton(text="⏳ To'lov Kutilmoqda"),
        ],
        [
            KeyboardButton(text="📢 Reklama Yuborish"),
            KeyboardButton(text="📨 Shaxsiy Xabar"),
        ],
        [
            KeyboardButton(text="⬅️ Admin Chiqish"),
        ],
    ],
    resize_keyboard=True,
)