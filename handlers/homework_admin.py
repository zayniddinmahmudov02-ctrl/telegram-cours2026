from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from config.settings import (
    HOMEWORK_ONLINE_CHANNEL_ID,
    HOMEWORK_VIDEO_CHANNEL_ID,
    HOMEWORK_SPEAKING_CHANNEL_ID,
)

from database import (
    homework,
    homework_files,
)

from keyboards.teacher_homework import (
    submission_actions_keyboard,
)

from states.homework import (
    HomeworkReviewState,
)

router = Router()
# =========================================================
# START REVIEW
# =========================================================

@router.message(F.text.startswith("/check"))
async def start_review(
    message: Message,
    state,
):

    if message.chat.type != "channel":
        return

    args = message.text.split()

    if len(args) != 2:

        await message.answer(
            "Foydalanish:\n"
            "/check SUBMISSION_ID"
        )

        return

    submission_id = int(args[1])

    submission = homework.get_submission(
        submission_id
    )

    if not submission:

        await message.answer(
            "Homework topilmadi."
        )

        return

    await state.set_state(
        HomeworkReviewState.waiting_score
    )

    await state.update_data(
        submission_id=submission_id,
    )

    await message.answer(
        f"""
📚 Homework

Level: {submission['level']}
Lesson: {submission['lesson']}
Component: {submission['component']}

Ballni kiriting (0-100).
"""
    )
# =========================================================
# SCORE
# =========================================================

@router.message(
    HomeworkReviewState.waiting_score,
    F.text,
)
async def review_score(
    message: Message,
    state,
):

    if not message.text.isdigit():

        await message.answer(
            "0-100 oralig'ida ball kiriting."
        )

        return

    score = int(message.text)

    if score < 0 or score > 100:

        await message.answer(
            "0-100 oralig'ida ball kiriting."
        )

        return

    await state.update_data(
        score=score,
    )

    await state.set_state(
        HomeworkReviewState.waiting_comment
    )

    await message.answer(
        "Izoh yozing."
    )
# =========================================================
# COMMENT
# =========================================================

@router.message(
    HomeworkReviewState.waiting_comment,
    F.text,
)
async def review_comment(
    message: Message,
    state,
    bot: Bot,
):

    data = await state.get_data()

    submission = homework.get_submission(
        data["submission_id"]
    )

    homework.approve_submission(
        submission_id=data["submission_id"],
        score=data["score"],
        comment=message.text,
        teacher_id=message.from_user.id,
    )

    await bot.send_message(
        submission["user_id"],
        f"""
✅ Homework tekshirildi

📚 {submission['level']}
📖 Lesson {submission['lesson']}
📝 {submission['component']}

⭐ Ball: {data['score']}/100

💬 Izoh:

{message.text}
"""
    )

    await state.clear()

    await message.answer(
        "✅ Homework baholandi."
    )
# =========================================================
# REJECT
# =========================================================

@router.message(F.text.startswith("/reject"))
async def reject_homework(
    message: Message,
):

    args = message.text.split()

    if len(args) < 3:

        await message.answer(
            "/reject ID Izoh"
        )

        return

    submission_id = int(args[1])

    comment = " ".join(args[2:])

    submission = homework.get_submission(
        submission_id
    )

    if not submission:

        await message.answer(
            "Homework topilmadi."
        )

        return

    homework.reject_submission(
        submission_id=submission_id,
        comment=comment,
        teacher_id=message.from_user.id,
    )

    await message.bot.send_message(
        submission["user_id"],
        f"""
❌ Homework rad etildi

📚 {submission['level']}
📖 Lesson {submission['lesson']}

Sabab:

{comment}
"""
    )

    await message.answer(
        "Homework rad etildi."
    )
# =========================================================
# OPEN REVIEW
# =========================================================

@router.callback_query(
    F.data.startswith("review:")
)
async def review(
    callback: CallbackQuery,
    state,
):

    submission_id = int(
        callback.data.split(":")[1]
    )

    submission = homework.get_submission(
        submission_id
    )

    if not submission:

        await callback.answer(
            "Homework topilmadi.",
            show_alert=True,
        )

        return

    await state.set_state(
        HomeworkReviewState.waiting_score
    )

    await state.update_data(
        submission_id=submission_id,
    )

    await callback.message.answer(
        f"""
📚 Homework

Level: {submission['level']}
Lesson: {submission['lesson']}
Component: {submission['component']}

0-100 ball kiriting.
"""
    )

    await callback.answer()
# =========================================================
# OPEN REJECT
# =========================================================

@router.callback_query(
    F.data.startswith("reject:")
)
async def reject(
    callback: CallbackQuery,
    state,
):

    submission_id = int(
        callback.data.split(":")[1]
    )

    await state.set_state(
        HomeworkReviewState.waiting_reject
    )

    await state.update_data(
        submission_id=submission_id,
    )

    await callback.message.answer(
        "Rad etish sababini yozing."
    )

    await callback.answer()
@router.message(
    HomeworkReviewState.waiting_reject
)
async def reject_comment(
    message: Message,
    state,
):

    data = await state.get_data()

    submission = homework.get_submission(
        data["submission_id"]
    )

    homework.reject_submission(
        submission_id=data["submission_id"],
        comment=message.text,
        teacher_id=message.from_user.id,
    )

    await message.bot.send_message(
        submission["user_id"],
        f"""
❌ Homework rad etildi

Sabab:

{message.text}
"""
    )

    await state.clear()

    await message.answer(
        "Homework rad etildi."
    )
