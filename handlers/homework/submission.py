# =========================================================
# HAUSAUFGABEN - SUBMISSION (upload -> confirm -> channel)
# =========================================================

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import LEVEL_ORDER
from database.homework import get_homework_category, get_membership
from database.homework_submissions import (
    add_submission_file,
    claim_submission_for_confirm,
    count_submission_files,
    delete_draft_submission,
    get_draft_submission,
    get_or_create_draft_submission,
    get_submission,
    get_submission_files,
    revert_submission_to_draft,
    set_submission_channel_message,
)
from keyboards.homework import (
    homework_confirm_keyboard,
    homework_upload_keyboard,
)
from keyboards.homework_admin import homework_score_keyboard
from keyboards.main import main_menu_for
from services.homework import (
    build_submission_header,
    is_menu_exit,
    normalize_level,
    parse_lesson_number,
)
from services.logger import logger
from states.homework import HomeworkSubmissionState

router = Router()

LEVEL_HINT = ", ".join(LEVEL_ORDER)

UPLOAD_INTRO = (
    "📤 <b>Vazifa yuborish</b>\n\n"
    "Quyidagilarni yuborishingiz mumkin:\n"
    "🎤 Audio\n"
    "📝 Matn\n"
    "🖼 Rasm\n"
    "📄 PDF\n\n"
)

FINISH_HINT = (
    "Barcha fayllarni yuklab bo'lgan bo'lsangiz, "
    "pastdagi «Vazifa yuborish» tugmasini bosing."
)


def _upload_prompt_text(file_count: int) -> str:
    return (
        f"{UPLOAD_INTRO}"
        f"✅ Yuklangan: {file_count} ta\n\n"
        f"{FINISH_HINT}"
    )


async def _show_upload_prompt(target, submission_id: int, file_count: int, *, edit: bool):
    text = _upload_prompt_text(file_count)
    keyboard = homework_upload_keyboard(submission_id)

    if edit:
        await target.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)


# =========================================================
# START / RESUME
# =========================================================
# Level/lesson belong to the submission, not the membership, so a
# brand-new submission asks for them first. An existing draft
# already has them recorded (from when it was created) and is
# resumed straight into uploading, skipping the prompt - this is
# also what makes "📤 Vazifa yuborish" resilient across a bot
# restart (FSM storage is in-memory, the draft row is not).

@router.callback_query(F.data.startswith("hw:submit:"))
async def homework_submit_start(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[2])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("❌ Avval kategoriyaga a'zo bo'ling.", show_alert=True)
        return

    draft = await get_draft_submission(callback.from_user.id, category_id)

    if draft:
        await state.set_state(HomeworkSubmissionState.uploading)
        await state.update_data(category_id=category_id, submission_id=draft["id"])

        file_count = await count_submission_files(draft["id"])
        await _show_upload_prompt(callback.message, draft["id"], file_count, edit=True)
        await callback.answer()
        return

    # Only reachable for Video/Online - Sprechen's category menu is
    # the dedicated 20-lesson grid (handlers.homework.sprechen),
    # which never generates a "hw:submit:" button, so this always
    # asks for a free-text level here.
    await state.set_state(HomeworkSubmissionState.waiting_level)
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(
        f"📊 Darajangizni kiriting ({LEVEL_HINT}):"
    )
    await callback.answer()


async def _bail_out(message: Message, state: FSMContext) -> bool:
    if not is_menu_exit(message.text):
        return False

    await state.clear()
    await message.answer(
        "🏠 Bosh menyu",
        reply_markup=main_menu_for(message.from_user.id),
    )
    return True


@router.message(HomeworkSubmissionState.waiting_level, F.text)
async def homework_submission_level(message: Message, state: FSMContext):
    if await _bail_out(message, state):
        return

    level = normalize_level(message.text)

    if level not in LEVEL_ORDER:
        await message.answer(f"❌ Noto'g'ri daraja. Masalan: {LEVEL_HINT}")
        return

    await state.update_data(level=level)
    await state.set_state(HomeworkSubmissionState.waiting_lesson)

    await message.answer("📖 Dars raqamini kiriting (masalan: 10):")


@router.message(HomeworkSubmissionState.waiting_lesson, F.text)
async def homework_submission_lesson(message: Message, state: FSMContext):
    if await _bail_out(message, state):
        return

    lesson = parse_lesson_number(message.text)

    if lesson is None:
        await message.answer("❌ Dars raqamini son ko'rinishida kiriting (masalan: 10).")
        return

    data = await state.get_data()
    category_id = data["category_id"]
    level = data["level"]

    membership = await get_membership(message.from_user.id, category_id)

    if not membership:
        await state.clear()
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return

    submission = await get_or_create_draft_submission(
        user_id=message.from_user.id,
        category_id=category_id,
        first_name=membership["first_name"],
        last_name=membership["last_name"],
        level=level,
        lesson_number=lesson,
    )

    await state.set_state(HomeworkSubmissionState.uploading)
    await state.update_data(category_id=category_id, submission_id=submission["id"])

    file_count = await count_submission_files(submission["id"])
    await _show_upload_prompt(message, submission["id"], file_count, edit=False)


# =========================================================
# UPLOAD HANDLERS
# =========================================================

async def _current_submission_id(message: Message, state: FSMContext) -> int | None:
    data = await state.get_data()
    submission_id = data.get("submission_id")

    if submission_id is None:
        await state.clear()
        await message.answer("❌ Sessiya tugadi. Qaytadan boshlang.")

    return submission_id


async def _after_upload(message: Message, submission_id: int):
    file_count = await count_submission_files(submission_id)
    await _show_upload_prompt(message, submission_id, file_count, edit=False)


@router.message(HomeworkSubmissionState.uploading, F.audio)
async def homework_upload_audio(message: Message, state: FSMContext):
    submission_id = await _current_submission_id(message, state)
    if submission_id is None:
        return

    await add_submission_file(
        submission_id,
        file_type="audio",
        file_id=message.audio.file_id,
        file_name=message.audio.file_name,
        mime_type=message.audio.mime_type,
        file_size=message.audio.file_size,
    )
    await _after_upload(message, submission_id)


@router.message(HomeworkSubmissionState.uploading, F.voice)
async def homework_upload_voice(message: Message, state: FSMContext):
    submission_id = await _current_submission_id(message, state)
    if submission_id is None:
        return

    await add_submission_file(
        submission_id,
        file_type="voice",
        file_id=message.voice.file_id,
        mime_type=message.voice.mime_type,
        file_size=message.voice.file_size,
    )
    await _after_upload(message, submission_id)


@router.message(HomeworkSubmissionState.uploading, F.photo)
async def homework_upload_photo(message: Message, state: FSMContext):
    submission_id = await _current_submission_id(message, state)
    if submission_id is None:
        return

    photo = message.photo[-1]

    await add_submission_file(
        submission_id,
        file_type="photo",
        file_id=photo.file_id,
        file_size=photo.file_size,
    )
    await _after_upload(message, submission_id)


@router.message(HomeworkSubmissionState.uploading, F.document)
async def homework_upload_document(message: Message, state: FSMContext):
    if message.document.mime_type != "application/pdf":
        await message.answer(
            "❌ Faqat PDF formatidagi fayl qabul qilinadi."
        )
        return

    submission_id = await _current_submission_id(message, state)
    if submission_id is None:
        return

    await add_submission_file(
        submission_id,
        file_type="pdf",
        file_id=message.document.file_id,
        file_name=message.document.file_name,
        mime_type=message.document.mime_type,
        file_size=message.document.file_size,
    )
    await _after_upload(message, submission_id)


@router.message(HomeworkSubmissionState.uploading, F.text)
async def homework_upload_text(message: Message, state: FSMContext):
    if is_menu_exit(message.text):
        # Leave the draft as-is - resuming "📤 Vazifa yuborish" later
        # picks it back up via get_or_create_draft_submission.
        await state.clear()
        return

    submission_id = await _current_submission_id(message, state)
    if submission_id is None:
        return

    text = message.text.strip()

    if not text:
        await message.answer("❌ Bo'sh matn yuborib bo'lmaydi.")
        return

    await add_submission_file(
        submission_id,
        file_type="text",
        text_content=text[:4000],
    )
    await _after_upload(message, submission_id)


@router.message(HomeworkSubmissionState.uploading)
async def homework_upload_unsupported(message: Message):
    await message.answer(
        "❌ Bu turdagi kontent qo'llab-quvvatlanmaydi.\n\n"
        "Audio, rasm, PDF yoki matn yuboring."
    )


# =========================================================
# FINISH -> CONFIRMATION SUMMARY
# =========================================================

@router.callback_query(F.data.startswith("hw:finish:"))
async def homework_finish(callback: CallbackQuery):
    submission_id = int(callback.data.split(":")[2])

    submission = await get_submission(submission_id)

    if not submission or submission["user_id"] != callback.from_user.id:
        await callback.answer("❌ Vazifa topilmadi.", show_alert=True)
        return

    if submission["status"] != "draft":
        await callback.answer("⚠️ Bu vazifa allaqachon yuborilgan.", show_alert=True)
        return

    file_count = await count_submission_files(submission_id)

    if file_count == 0:
        await callback.answer(
            "❌ Kamida bitta fayl yoki matn yuklang.",
            show_alert=True,
        )
        return

    category = await get_homework_category(submission["category_id"])

    text = (
        "📋 <b>Tasdiqlash</b>\n\n"
        f"📚 <b>Kategoriya:</b> {category['name']}\n"
        f"📊 <b>Daraja:</b> {submission['level']}\n"
        f"📖 <b>Dars:</b> {submission['lesson_number']}-dars\n"
        f"👤 <b>Ism:</b> {submission['first_name']}\n"
        f"👤 <b>Familiya:</b> {submission['last_name']}\n"
        f"📎 <b>Fayllar soni:</b> {file_count}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_confirm_keyboard(submission_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hw:continue:"))
async def homework_continue(callback: CallbackQuery, state: FSMContext):
    submission_id = int(callback.data.split(":")[2])

    submission = await get_submission(submission_id)

    if (
        not submission
        or submission["user_id"] != callback.from_user.id
        or submission["status"] != "draft"
    ):
        await callback.answer("❌ Vazifa topilmadi.", show_alert=True)
        return

    await state.set_state(HomeworkSubmissionState.uploading)
    await state.update_data(
        category_id=submission["category_id"],
        submission_id=submission_id,
    )

    file_count = await count_submission_files(submission_id)
    await _show_upload_prompt(callback.message, submission_id, file_count, edit=True)
    await callback.answer()


# =========================================================
# CANCEL
# =========================================================

@router.callback_query(F.data.startswith("hw:cancel:"))
async def homework_cancel(callback: CallbackQuery, state: FSMContext):
    submission_id = int(callback.data.split(":")[2])

    submission = await get_submission(submission_id)

    if not submission or submission["user_id"] != callback.from_user.id:
        await callback.answer("❌ Vazifa topilmadi.", show_alert=True)
        return

    if submission["status"] != "draft":
        await callback.answer(
            "⚠️ Bu vazifa allaqachon yuborilgan, bekor qilib bo'lmaydi.",
            show_alert=True,
        )
        return

    category_id = submission["category_id"]

    await delete_draft_submission(submission_id)
    await state.clear()

    category = await get_homework_category(category_id)

    if category["code"] == "sprechen":
        from handlers.homework.sprechen import render_sprechen_menu

        membership = await get_membership(callback.from_user.id, category_id)
        await render_sprechen_menu(callback, category_id, callback.from_user.id, membership)
    else:
        from handlers.homework.access import render_category_menu

        await render_category_menu(callback, category_id, category["name"])

    await callback.answer("❌ Bekor qilindi.")


# =========================================================
# CONFIRM -> SEND TO CHANNEL
# =========================================================

_SENDERS = {
    "audio": lambda bot, chat_id, f, caption: bot.send_audio(chat_id, f["file_id"], caption=caption),
    "voice": lambda bot, chat_id, f, caption: bot.send_voice(chat_id, f["file_id"], caption=caption),
    "photo": lambda bot, chat_id, f, caption: bot.send_photo(chat_id, f["file_id"], caption=caption),
    "pdf": lambda bot, chat_id, f, caption: bot.send_document(chat_id, f["file_id"], caption=caption),
}


@router.callback_query(F.data.startswith("hw:confirm:"))
async def homework_confirm(callback: CallbackQuery, state: FSMContext):
    submission_id = int(callback.data.split(":")[2])

    submission = await get_submission(submission_id)

    if not submission or submission["user_id"] != callback.from_user.id:
        await callback.answer("❌ Vazifa topilmadi.", show_alert=True)
        return

    # Duplicate-confirmation guard - a second tap after status has
    # already moved past 'draft' is a no-op, not a re-send.
    if submission["status"] != "draft":
        await callback.answer("⚠️ Bu vazifa allaqachon yuborilgan.", show_alert=True)
        return

    files = await get_submission_files(submission_id)

    if not files:
        await callback.answer("❌ Kamida bitta fayl yoki matn yuklang.", show_alert=True)
        return

    # Atomic claim - the real guard against a double-tap producing
    # two channel posts (see claim_submission_for_confirm).
    claimed = await claim_submission_for_confirm(submission_id)

    if not claimed:
        await callback.answer("⚠️ Bu vazifa allaqachon yuborilgan.", show_alert=True)
        return

    category = await get_homework_category(submission["category_id"])
    channel_id = category["channel_id"]

    header_text = build_submission_header(
        submission_uid=submission["submission_uid"],
        first_name=submission["first_name"],
        last_name=submission["last_name"],
        category_name=category["name"],
        level=submission["level"],
        lesson_number=submission["lesson_number"],
        user_id=submission["user_id"],
        file_count=len(files),
        created_at=submission["created_at"],
        level_label="Guruh" if category["code"] == "sprechen" else "Daraja",
        gender=submission["gender"],
    )

    try:
        header_message = await callback.bot.send_message(
            chat_id=channel_id,
            text=header_text,
            parse_mode="HTML",
            reply_markup=homework_score_keyboard(submission_id),
        )

        total = len(files)

        for index, item in enumerate(files, start=1):
            caption = f"📎 {submission['submission_uid']} — {index}/{total}"

            sender = _SENDERS.get(item["file_type"])

            if sender:
                await sender(callback.bot, channel_id, item, caption)
            else:
                # text entries
                await callback.bot.send_message(
                    chat_id=channel_id,
                    text=f"{caption}\n\n{item['text_content']}",
                )

    except Exception as e:
        logger.error(
            f"Homework submission channel send failed "
            f"(submission={submission_id}, channel={channel_id}): {e}"
        )
        # Undo the claim so the draft (and its files) survive and
        # the user can retry, instead of being stuck 'submitted'
        # with nothing actually posted to the channel.
        await revert_submission_to_draft(submission_id)
        await callback.answer(
            "❌ Yuborishda xatolik yuz berdi. Qaytadan urinib ko'ring.",
            show_alert=True,
        )
        return

    await set_submission_channel_message(submission_id, channel_id, header_message.message_id)
    await state.clear()

    await callback.message.edit_text(
        "✅ <b>Vazifangiz muvaffaqiyatli yuborildi!</b>\n\n"
        "⏳ Administrator tekshirib, baholaydi.",
        parse_mode="HTML",
    )
    await callback.answer()
