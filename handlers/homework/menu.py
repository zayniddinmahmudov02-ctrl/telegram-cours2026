# =========================================================
# HAUSAUFGABEN - CATEGORY MENU / TOTAL SCORE
# =========================================================

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.homework import get_homework_category, get_membership
from database.homework_evaluations import get_user_score_summary
from keyboards.homework import homework_back_to_menu_keyboard, homework_menu_keyboard

router = Router()


@router.callback_query(F.data.startswith("hw:menu:"))
async def homework_menu(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[2])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("❌ Avval kategoriyaga a'zo bo'ling.", show_alert=True)
        return

    category = await get_homework_category(category_id)

    await callback.message.edit_text(
        f"📚 <b>{category['name']}</b>\n\nBo'limni tanlang.",
        parse_mode="HTML",
        reply_markup=homework_menu_keyboard(category_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hw:total:"))
async def homework_total_score(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[2])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("❌ Avval kategoriyaga a'zo bo'ling.", show_alert=True)
        return

    summary = await get_user_score_summary(callback.from_user.id)

    text = (
        f"🏆 <b>Umumiy ball:</b> {summary['total_score']}\n\n"
        f"📋 <b>Baholangan vazifalar:</b> {summary['evaluated_count']}\n"
    )

    if summary["average"] is not None:
        text += f"📊 <b>O'rtacha ball:</b> {summary['average']}\n"

    if summary["by_category"]:
        text += "\n"
        for row in summary["by_category"]:
            text += f"{row['category_name']}: {row['total_score']}\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_back_to_menu_keyboard(category_id),
    )
    await callback.answer()
