# =========================================================
# HAUSAUFGABEN - ACCEPTED HOMEWORK HISTORY
# =========================================================

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.homework import get_membership
from database.homework_submissions import count_user_submissions, get_user_submissions
from keyboards.homework import homework_history_keyboard
from services.homework import status_label

router = Router()

PAGE_SIZE = 5

# Everything except an unconfirmed draft counts as "history".
VISIBLE_STATUSES = ("submitted", "revision_required", "accepted", "excellent")


@router.callback_query(F.data.startswith("hw:history:"))
async def homework_history(callback: CallbackQuery):
    parts = callback.data.split(":")
    category_id = int(parts[2])
    page = int(parts[3])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("❌ Avval kategoriyaga a'zo bo'ling.", show_alert=True)
        return

    total = await count_user_submissions(
        callback.from_user.id, category_id, VISIBLE_STATUSES
    )

    if total == 0:
        await callback.message.edit_text(
            "📋 <b>Qabul qilingan vazifalar</b>\n\n"
            "Sizda hozircha yuborilgan vazifalar mavjud emas.",
            parse_mode="HTML",
            reply_markup=homework_history_keyboard(category_id, 0, 1),
        )
        await callback.answer()
        return

    total_pages = max(1, -(-total // PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))

    submissions = await get_user_submissions(
        callback.from_user.id,
        category_id,
        VISIBLE_STATUSES,
        limit=PAGE_SIZE,
        offset=page * PAGE_SIZE,
    )

    text = "📋 <b>Qabul qilingan vazifalar</b>\n\n"

    for s in submissions:
        score_line = f"⭐ Ball: {s['score']}/5\n" if s["score"] is not None else ""

        text += (
            f"📖 {s['lesson_number']}-dars ({s['level']})\n"
            f"{score_line}"
            f"{status_label(s['status'])}\n"
            f"🕐 {s['created_at'].strftime('%d.%m.%Y')}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_history_keyboard(category_id, page, total_pages),
    )
    await callback.answer()
