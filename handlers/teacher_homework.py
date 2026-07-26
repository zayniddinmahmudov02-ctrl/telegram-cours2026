# =========================================================
# IMPORTS
# =========================================================

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.fsm.context import FSMContext

from database import homework
from database import homework_files

from keyboards.teacher_homework import (
    pending_homeworks_keyboard,
    submission_actions_keyboard,
)

from states.homework import TeacherHomeworkState
# =========================================================
# ROUTER
# =========================================================

router = Router()


# =========================================================
# CONSTANTS
# =========================================================

PENDING_EMPTY_TEXT = (
    "✅ <b>Kutilayotgan homework mavjud emas.</b>"
)

PENDING_LIST_TEXT = (
    "📥 <b>Kutilayotgan Homeworklar</b>\n\n"
    "Tekshirish uchun talabani tanlang."
)


# =========================================================
# PENDING HOMEWORKS
# =========================================================

async def load_pending_homeworks(
    callback: CallbackQuery,
):

    submissions = homework.get_pending_submissions()

    if not submissions:
        await callback.message.edit_text(
            PENDING_EMPTY_TEXT
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        PENDING_LIST_TEXT,
        reply_markup=pending_homeworks_keyboard(
            submissions
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data == "teacher_homeworks"
)
async def teacher_homeworks(
    callback: CallbackQuery,
):

    await load_pending_homeworks(
        callback
    )


@router.callback_query(
    F.data == "teacher_homeworks_refresh"
)
async def refresh_teacher_homeworks(
    callback: CallbackQuery,
):

    await load_pending_homeworks(
        callback
    )
# =========================================================
# HOMEWORK DETAIL
# =========================================================

async def open_submission(
    callback: CallbackQuery,
    submission_id: int,
):

    submission = homework.get_submission(
        submission_id
    )

    if not submission:
        await callback.answer(
            "Homework topilmadi.",
            show_alert=True,
        )
        return

    files = homework_files.get_files(
        submission_id
    )

    await callback.message.edit_text(
        format_submission_detail(
            submission,
            len(files),
        ),
        reply_markup=submission_actions_keyboard(
            submission_id
        ),
    )

    await callback.answer()

    for file in files:
        await send_homework_file(
            callback.bot,
            callback.message.chat.id,
            file,
        )


@router.callback_query(
    F.data.startswith("teacher_submission:")
)
async def teacher_submission(
    callback: CallbackQuery,
):

    submission_id = int(
        callback.data.split(":")[1]
    )

    await open_submission(
        callback,
        submission_id,
    )
# =========================================================
# APPROVE / REJECT
# =========================================================

async def update_submission_status(
    callback: CallbackQuery,
    state: FSMContext,
    status: str,
):

    submission_id = int(
        callback.data.split(":")[1]
    )

    await state.update_data(
        submission_id=submission_id,
        status=status,
    )

    await state.set_state(
        TeacherHomeworkState.waiting_comment
    )

    action = (
        "tasdiqlash"
        if status == "approved"
        else "rad etish"
    )

    await callback.message.edit_text(
        f"💬 Homeworkni <b>{action}</b> uchun izoh yozing.\n\n"
        "Izoh yuboring yoki '-' yuborib izohsiz davom eting."
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("teacher_approve:")
)
async def approve_submission(
    callback: CallbackQuery,
    state: FSMContext,
):

    await update_submission_status(
        callback,
        state,
        "approved",
    )


@router.callback_query(
    F.data.startswith("teacher_reject:")
)
async def reject_submission(
    callback: CallbackQuery,
    state: FSMContext,
):

    await update_submission_status(
        callback,
        state,
        "rejected",
    )
# =========================================================
# TEACHER COMMENT
# =========================================================

@router.message(
    TeacherHomeworkState.waiting_comment
)
async def save_teacher_comment(
    message: Message,
    state: FSMContext,
):

    data = await state.get_data()

    submission_id = data["submission_id"]
    status = data["status"]

    comment = (
        None
        if message.text.strip() == "-"
        else message.text.strip()
    )

    if status == "approved":
        homework.approve_submission(
            submission_id=submission_id,
            checked_by=message.from_user.id,
            teacher_comment=comment,
        )
    else:
        homework.reject_submission(
            submission_id=submission_id,
            checked_by=message.from_user.id,
            teacher_comment=comment,
        )

    submission = homework.get_submission(
        submission_id
    )

    await notify_student(
        message.bot,
        submission,
        status,
        comment,
    )

    await state.clear()

    await message.answer(
        "✅ Homework muvaffaqiyatli tekshirildi."
    )
# =========================================================
# HELPERS
# =========================================================

COMPONENT_NAMES = {
    "grammar": "📖 Grammatik",
    "reading": "📚 Lesen",
    "listening": "🎧 Hören",
    "writing": "✍️ Schreiben",
    "speaking": "🗣 Sprechen",
    "vocabulary": "📖 Wortschatz",
}

STATUS_NAMES = {
    "pending": "⏳ Kutilmoqda",
    "approved": "✅ Tasdiqlandi",
    "rejected": "❌ Rad etildi",
}


def component_name(component: str) -> str:
    return COMPONENT_NAMES.get(component, component)


def status_name(status: str) -> str:
    return STATUS_NAMES.get(status, status)


def format_submission_detail(
    submission: dict,
    files_count: int,
) -> str:

    return (
        "📄 <b>HOMEWORK</b>\n\n"
        f"👤 <b>Student ID:</b> <code>{submission['user_id']}</code>\n"
        f"🎓 <b>Level:</b> {submission['level']}\n"
        f"📖 <b>Lesson:</b> {submission['lesson']}\n"
        f"📚 <b>Component:</b> {component_name(submission['component'])}\n"
        f"📎 <b>Files:</b> {files_count}\n"
        f"📅 <b>Created:</b> {submission['created_at']}\n"
        f"📌 <b>Status:</b> {status_name(submission['status'])}"
    )


async def notify_student(
    bot,
    submission: dict,
    status: str,
    comment: str | None,
):
    text = (
        "📄 <b>Homework natijasi</b>\n\n"
        f"🎓 Level: <b>{submission['level']}</b>\n"
        f"📖 Lesson: <b>{submission['lesson']}</b>\n"
        f"📚 Component: {component_name(submission['component'])}\n\n"
        f"📌 Natija: <b>{status_name(status)}</b>"
    )

    if comment:
        text += (
            f"\n\n💬 <b>Teacher izohi:</b>\n"
            f"{comment}"
        )

    await bot.send_message(
        chat_id=submission["user_id"],
        text=text,
    )


async def send_homework_file(
    bot,
    chat_id: int,
    file: dict,
):

    file_type = file["file_type"]
    file_id = file["telegram_file_id"]

    if file_type == "photo":
        await bot.send_photo(
            chat_id,
            file_id,
        )

    elif file_type == "document":
        await bot.send_document(
            chat_id,
            file_id,
        )

    elif file_type == "audio":
        await bot.send_audio(
            chat_id,
            file_id,
        )

    elif file_type == "voice":
        await bot.send_voice(
            chat_id,
            file_id,
        )
