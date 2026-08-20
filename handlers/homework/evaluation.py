# =========================================================
# HAUSAUFGABEN - ADMIN SCORING
# =========================================================
# Fired from the score buttons attached to the channel post (see
# handlers.homework.submission) AND from the Admin Panel's
# submission detail view (handlers.homework.admin) - same
# callback_data shape, same handler, since re-scoring is just
# another save_evaluation UPSERT either way.

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.homework import get_homework_category
from database.homework_evaluations import save_evaluation
from database.homework_submissions import get_submission, set_submission_status
from services.auth import is_admin
from services.homework import build_result_message, score_label, score_to_result_status
from services.logger import logger

router = Router()


@router.callback_query(F.data.startswith("hw:eval:"))
async def homework_evaluate(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return

    parts = callback.data.split(":")
    submission_id = int(parts[2])
    score = int(parts[3])

    submission = await get_submission(submission_id)

    if not submission:
        await callback.answer("❌ Vazifa topilmadi.", show_alert=True)
        return

    if submission["status"] == "draft":
        await callback.answer("⚠️ Vazifa hali yuborilmagan.", show_alert=True)
        return

    result_status = score_to_result_status(score)

    await save_evaluation(
        submission_id=submission_id,
        score=score,
        result_status=result_status,
        evaluator_id=callback.from_user.id,
    )
    await set_submission_status(submission_id, result_status)

    # Reflect the current score on the channel post itself, keyboard
    # left in place so the admin can correct it later if needed.
    try:
        current_text = callback.message.text or callback.message.caption or ""

        if "✅ Baholandi:" not in current_text:
            current_text += f"\n\n✅ Baholandi: {score}/5 - {score_label(score)}"
        else:
            current_text = current_text.split("\n\n✅ Baholandi:")[0]
            current_text += f"\n\n✅ Baholandi: {score}/5 - {score_label(score)}"

        await callback.message.edit_text(
            current_text,
            parse_mode="HTML",
            reply_markup=callback.message.reply_markup,
        )
    except Exception as e:
        logger.error(f"Homework channel post update failed (submission={submission_id}): {e}")

    # Notify the user
    category = await get_homework_category(submission["category_id"])
    category_name = category["name"] if category else "-"

    try:
        await callback.bot.send_message(
            chat_id=submission["user_id"],
            text=build_result_message(
                category_name=category_name,
                lesson_number=submission["lesson_number"],
                score=score,
            ),
        )
    except Exception as e:
        logger.error(
            f"Homework result notification failed "
            f"(submission={submission_id}, user={submission['user_id']}): {e}"
        )

    await callback.answer(f"✅ Baholandi: {score}/5")
