# =========================================================
# HAUSAUFGABEN - SPRECHEN GURUH (dedicated flow)
# =========================================================
# Sprechen replaces the generic "free level/lesson per submission"
# model with: gender + one fixed level_group permanently on the
# membership (registered once), and a fixed 20-lesson grid instead
# of a free-text lesson number. Everything below "a lesson is
# selected" - upload, finish, confirm, channel routing, admin
# scoring - reuses the existing, unmodified generic machinery in
# handlers.homework.submission/evaluation, since a Sprechen draft
# is just a homework_submissions row like any other.

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import SPRECHEN_GROUP_LINKS
from database.homework import get_membership
from database.homework_evaluations import get_sprechen_progress
from database.homework_submissions import (
    count_submission_files,
    get_or_create_draft_submission_for_lesson,
)
from keyboards.homework import homework_upload_keyboard
from keyboards.sprechen import (
    sprechen_back_to_menu_keyboard,
    sprechen_gender_keyboard,
    sprechen_lesson_grid_keyboard,
    sprechen_level_group_keyboard,
)
from services.homework import (
    GENDER_LABELS,
    LEVEL_GROUP_LABELS,
    SPRECHEN_LESSON_COUNT,
    is_valid_gender,
    is_valid_level_group,
    is_valid_sprechen_lesson,
)
from states.homework import HomeworkProfileState, HomeworkSubmissionState

router = Router()


# =========================================================
# REGISTRATION - START (called from access.py after password)
# =========================================================

async def start_sprechen_registration(message: Message, state: FSMContext, category_id: int):
    await state.set_state(None)
    await state.update_data(category_id=category_id)

    await message.answer(
        "⚥ <b>Jinsingizni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=sprechen_gender_keyboard(category_id),
    )


@router.callback_query(F.data.startswith("hw:sp:gender:"))
async def sprechen_gender_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    category_id = int(parts[3])
    gender = parts[4]

    if not is_valid_gender(gender):
        await callback.answer("❌ Noto'g'ri tanlov.", show_alert=True)
        return

    await callback.message.edit_text(
        "📊 <b>Darajangizni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=sprechen_level_group_keyboard(category_id, gender),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hw:sp:level:"))
async def sprechen_level_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    category_id = int(parts[3])
    gender = parts[4]
    level_group = parts[5]

    if not is_valid_gender(gender) or not is_valid_level_group(level_group):
        await callback.answer("❌ Noto'g'ri tanlov.", show_alert=True)
        return

    # Hands off into the existing, unmodified first/last-name FSM
    # steps (handlers.homework.profile) - gender/level_group ride
    # along in FSM data and homework_profile_last_name's finalize
    # step reads them back to branch into finish_sprechen_registration.
    await state.set_state(HomeworkProfileState.waiting_first_name)
    await state.update_data(
        category_id=category_id,
        mode="create",
        gender=gender,
        level_group=level_group,
    )

    await callback.message.edit_text("👤 Ismingizni kiriting:")
    await callback.answer()


# =========================================================
# REGISTRATION - FINISH (called from profile.py's finalize step)
# =========================================================

async def finish_sprechen_registration(
    message: Message,
    category_id: int,
    category_name: str,
    gender: str,
    level_group: str,
    first_name: str,
    last_name: str,
):
    link = SPRECHEN_GROUP_LINKS.get((gender, level_group))

    text = f"✅ Tabriklaymiz! <b>{category_name}</b> bo'limiga muvaffaqiyatli qo'shildingiz."

    if link:
        text += f"\n\n🔗 Guruhga qo'shilish uchun havola:\n{link}"

    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

    membership = {
        "first_name": first_name,
        "last_name": last_name,
        "gender": gender,
        "level_group": level_group,
    }

    await render_sprechen_menu(message, category_id, message.from_user.id, membership)


# =========================================================
# LESSON GRID
# =========================================================

async def render_sprechen_menu(target, category_id: int, user_id: int, membership: dict):
    progress = await get_sprechen_progress(user_id, category_id)
    completed = {row["lesson_number"] for row in progress if row["score"] >= 4}

    text = (
        f"📚 <b>Hausaufgaben — Sprechen</b>\n\n"
        f"{membership['first_name']} {membership['last_name']} "
        f"({LEVEL_GROUP_LABELS.get(membership['level_group'], membership['level_group'])})"
    )
    keyboard = sprechen_lesson_grid_keyboard(category_id, completed)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("hw:sp:menu:"))
async def sprechen_menu_callback(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[3])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership or not membership.get("level_group"):
        await callback.answer("❌ Avval ro'yxatdan o'ting.", show_alert=True)
        return

    await render_sprechen_menu(callback, category_id, callback.from_user.id, membership)
    await callback.answer()


# =========================================================
# LESSON SELECT -> UPLOAD (reuses the existing generic upload/
# finish/confirm/cancel/continue machinery in handlers.homework.
# submission unmodified - only entry differs)
# =========================================================

LESSON_UPLOAD_FILE_TYPES = (
    "Quyidagilarni yuborishingiz mumkin:\n"
    "🎤 Audio\n"
    "📝 Matn\n"
    "🖼 Rasm\n"
    "📄 PDF\n\n"
)


def _sprechen_upload_prompt_text(lesson_number: int, file_count: int) -> str:
    return (
        f"📖 <b>{lesson_number}-dars vazifasini yuboring.</b>\n\n"
        f"{LESSON_UPLOAD_FILE_TYPES}"
        f"✅ Yuklangan: {file_count} ta\n\n"
        f"Barcha fayllarni yuklab bo'lgan bo'lsangiz, "
        f"pastdagi «Vazifa yuborish» tugmasini bosing."
    )


@router.callback_query(F.data.startswith("hw:sp:lesson:"))
async def sprechen_lesson_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    category_id = int(parts[3])
    lesson_number = int(parts[4])

    if not is_valid_sprechen_lesson(lesson_number):
        await callback.answer("❌ Noto'g'ri dars.", show_alert=True)
        return

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership or not membership.get("gender") or not membership.get("level_group"):
        await callback.answer("❌ Avval ro'yxatdan o'ting.", show_alert=True)
        return

    submission = await get_or_create_draft_submission_for_lesson(
        user_id=callback.from_user.id,
        category_id=category_id,
        first_name=membership["first_name"],
        last_name=membership["last_name"],
        level=membership["level_group"],
        lesson_number=lesson_number,
        gender=membership["gender"],
    )

    await state.set_state(HomeworkSubmissionState.uploading)
    await state.update_data(category_id=category_id, submission_id=submission["id"])

    file_count = await count_submission_files(submission["id"])

    await callback.message.edit_text(
        _sprechen_upload_prompt_text(lesson_number, file_count),
        parse_mode="HTML",
        reply_markup=homework_upload_keyboard(submission["id"]),
    )
    await callback.answer()


# =========================================================
# PROFILE (view-only - editing wasn't requested for Sprechen)
# =========================================================

@router.callback_query(F.data.startswith("hw:sp:profile:"))
async def sprechen_profile_view(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[3])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership or not membership.get("level_group"):
        await callback.answer("❌ Avval ro'yxatdan o'ting.", show_alert=True)
        return

    text = (
        "⚙️ <b>Profil</b>\n\n"
        f"👤 <b>Ism:</b> {membership['first_name']}\n"
        f"👤 <b>Familiya:</b> {membership['last_name']}\n"
        f"⚥ <b>Jins:</b> {GENDER_LABELS.get(membership['gender'], '-')}\n"
        f"📊 <b>Daraja guruhi:</b> {LEVEL_GROUP_LABELS.get(membership['level_group'], '-')}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=sprechen_back_to_menu_keyboard(category_id),
    )
    await callback.answer()


# =========================================================
# TOTAL SCORE
# =========================================================

@router.callback_query(F.data.startswith("hw:sp:total:"))
async def sprechen_total_score(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[3])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership or not membership.get("level_group"):
        await callback.answer("❌ Avval ro'yxatdan o'ting.", show_alert=True)
        return

    progress = await get_sprechen_progress(callback.from_user.id, category_id)

    total_score = sum(row["score"] for row in progress)
    completed_count = sum(1 for row in progress if row["score"] >= 4)
    evaluated_count = len(progress)
    average = round(total_score / evaluated_count, 1) if evaluated_count else None

    text = (
        "🏆 <b>Umumiy ball</b>\n\n"
        f"📚 Bajarilgan darslar: {completed_count}/{SPRECHEN_LESSON_COUNT}\n"
        f"⭐ Umumiy ball: {total_score}\n"
    )

    if average is not None:
        text += f"📊 O'rtacha ball: {average}\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=sprechen_back_to_menu_keyboard(category_id),
    )
    await callback.answer()
