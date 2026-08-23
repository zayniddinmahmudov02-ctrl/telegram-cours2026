# =========================================================
# HAUSAUFGABEN - ADMIN SCORING
# =========================================================
# Fired from the score buttons attached to the channel post (see
# handlers.homework.submission) AND from the Admin Panel's
# submission detail view (handlers.homework.admin) - same
# callback_data shape, same handler, since re-scoring is just
# another save_evaluation UPSERT either way.
#
# The channel post is always updated by chat_id/message_id stored
# on the submission (submission["channel_id"]/["channel_message_id"]),
# never by editing callback.message directly - when this fires from
# the Admin Panel, callback.message is the admin's own private
# detail view, not the channel post, so editing it would silently
# leave the channel post stale. Telegram also has no "read current
# message text" API, so the full header is rebuilt from submission
# data on every score rather than string-patching old text.

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.homework import get_homework_category
from database.homework_evaluations import save_evaluation
from database.homework_submissions import (
    count_submission_files,
    get_submission,
    set_submission_status,
)
from keyboards.homework_admin import homework_score_keyboard
from services.auth import is_admin
from services.homework import (
    build_result_message,
    build_submission_header,
    score_label,
    score_to_result_status,
)
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

    category = await get_homework_category(submission["category_id"])
    result_status = score_to_result_status(score)

    await save_evaluation(
        submission_id=submission_id,
        score=score,
        result_status=result_status,
        evaluator_id=callback.from_user.id,
    )
    await set_submission_status(submission_id, result_status)

    # Update the real channel post (by stored id, not callback.message)
    if submission["channel_id"] and submission["channel_message_id"]:
        try:
            file_count = await count_submission_files(submission_id)

            header_text = build_submission_header(
                submission_uid=submission["submission_uid"],
                first_name=submission["first_name"],
                last_name=submission["last_name"],
                category_name=category["name"] if category else "-",
                level=submission["level"],
                lesson_number=submission["lesson_number"],
                user_id=submission["user_id"],
                file_count=file_count,
                created_at=submission["created_at"],
                level_label="Guruh" if category and category["code"] == "sprechen" else "Daraja",
                gender=submission["gender"],
            )
            header_text += f"\n\n✅ Baholandi: {score}/5 - {score_label(score)}"

            await callback.bot.edit_message_text(
                chat_id=submission["channel_id"],
                message_id=submission["channel_message_id"],
                text=header_text,
                parse_mode="HTML",
                reply_markup=homework_score_keyboard(submission_id),
            )
        except Exception as e:
            logger.error(
                f"Homework channel post update failed (submission={submission_id}): {e}"
            )
    else:
        logger.error(
            f"Homework submission has no channel_id/channel_message_id "
            f"(submission={submission_id})"
        )

    # If this fired from the Admin Panel's own detail message (not
    # the channel), give the admin inline confirmation there too.
    try:
        if callback.message.chat.id != submission["channel_id"]:
            await callback.message.answer(
                f"✅ Baholandi: {score}/5 - {score_label(score)}"
            )
    except Exception:
        pass

    # Notify the user
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
