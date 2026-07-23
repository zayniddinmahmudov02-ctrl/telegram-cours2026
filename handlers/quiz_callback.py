from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.quiz import (
    send_next_question,
    finish_quiz,
    start_quiz_block,
)

from handlers.wordgame import build_level_menu

from config import (
    quiz_sessions,
    quiz_running,
    active_questions,
    answered_users,
)

router = Router()
@router.callback_query(F.data.startswith("quiz:"))
async def quiz_answer(callback: CallbackQuery):

    user_id = callback.from_user.id

    data_parts = callback.data.split(":", 2)

    if len(data_parts) < 3:
        await callback.answer(
            "❌ Callback xatosi.",
            show_alert=True
        )
        return

    qid = data_parts[1]
    answer_key = data_parts[2]

    question_data = active_questions.get(qid)
    session = quiz_sessions.get(user_id)

    if not question_data or not session:
        await callback.answer(
            "❌ Test seansi tugagan yoki eskirgan.",
            show_alert=True
        )
        return

    if user_id in answered_users.get(qid, set()):
        await callback.answer(
            "❌ Siz allaqachon javob bergansiz.",
            show_alert=True
        )
        return

    answered_users.setdefault(
        qid,
        set()
    ).add(user_id)

    correct = question_data["correct"]

    selected = question_data["answers"].get(
        answer_key
    )

    if selected == correct:

        session["score"] += 1

        await callback.answer(
            "✅ To'g'ri!"
        )

    else:

        await callback.answer(
            f"❌ Noto'g'ri!\n\n"
            f"✅ {correct}",
            show_alert=True
        )

    session["index"] += 1

    active_questions.pop(qid, None)
    answered_users.pop(qid, None)

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await send_next_question(
        callback.message.chat.id,
        user_id
    )

# =========================================================
# RESTART QUIZ
# =========================================================

@router.callback_query(F.data.startswith("restartquiz:"))
async def restart_quiz_handler(callback: CallbackQuery):

    user_id = callback.from_user.id

    # Tozalash
    quiz_running.discard(user_id)
    quiz_sessions.pop(user_id, None)

    prefix = f"{user_id}_"

    for key in [
        k
        for k in active_questions
        if k.startswith(prefix)
    ]:
        active_questions.pop(key, None)
        answered_users.pop(key, None)

    parts = callback.data.split(":")

    if len(parts) != 3:

        await callback.answer(
            "❌ Callback xatosi.",
            show_alert=True
        )

        return

    level = parts[1]
    block = int(parts[2])

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer(
        "🔄 Test qayta boshlandi."
    )

    await start_quiz_block(
        message=callback.message,
        level=level,
        block=block,
        force_restart=True,
        user_id=user_id
    )


# =========================================================
# CANCEL QUIZ
# =========================================================

@router.callback_query(F.data == "cancelquiz")
async def cancel_quiz_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    menu = await build_level_menu(
        callback.from_user.id
    )

    await callback.message.answer(
        "🎮 WortSpiel\n\nDarajani tanlang:",
        reply_markup=menu
    )

    await callback.answer()


# =========================================================
# STOP QUIZ
# =========================================================

@router.callback_query(F.data.startswith("stopquiz:"))
async def stop_quiz(callback: CallbackQuery):

    try:
        user_id = int(
            callback.data.split(":")[1]
        )

    except (IndexError, ValueError):
        return

    if callback.from_user.id != user_id:

        await callback.answer(
            "❌ Bu sizning testingiz emas.",
            show_alert=True
        )

        return

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await finish_quiz(
        callback.message.chat.id,
        user_id
    )
