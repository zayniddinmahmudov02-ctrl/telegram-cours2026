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
from database.homework import (
    get_homework_category,
    get_membership,
    set_membership_access_password,
)
from database.homework_evaluations import get_sprechen_progress
from database.homework_submissions import (
    count_submission_files,
    get_or_create_draft_submission_for_lesson,
)
from keyboards.homework import homework_password_cancel_keyboard, homework_upload_keyboard
from keyboards.main import main_menu_for
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
    is_menu_exit,
    is_sprechen_access_valid,
    is_valid_gender,
    is_valid_level_group,
    is_valid_sprechen_lesson,
)
from states.homework import HomeworkAccessState, HomeworkProfileState, HomeworkSubmissionState
from utils.security import verify_password

router = Router()


# =========================================================
# ACCESS FLOW: gender -> level -> password
# =========================================================
# A brand-new member goes through all three. A returning member
# whose access has gone stale (password rotated since they last
# verified it - see services.homework.is_sprechen_access_valid)
# already has gender/level_group on file, so they skip straight to
# the password step instead of being asked to pick a group again -
# level_group is meant to be stable once chosen, not something a
# lapsed password silently reopens for changing.

async def start_sprechen_access_flow(
    target,
    state: FSMContext,
    category_id: int,
    membership: dict | None,
):
    if membership and membership.get("gender") and membership.get("level_group"):
        await _prompt_sprechen_password(target, state, category_id)
        return

    await state.set_state(None)
    await state.update_data(category_id=category_id)

    text = "⚥ <b>Jinsingizni tanlang:</b>"
    keyboard = sprechen_gender_keyboard(category_id)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)


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

    await state.update_data(category_id=category_id, gender=gender, level_group=level_group)
    await _prompt_sprechen_password(callback, state, category_id)
    await callback.answer()


async def _prompt_sprechen_password(target, state: FSMContext, category_id: int):
    category = await get_homework_category(category_id)

    if not category or not category["password_hash"]:
        text = (
            "⚠️ Bu guruh uchun parol hali sozlanmagan. "
            "Administrator bilan bog'laning."
        )

        if isinstance(target, CallbackQuery):
            await target.answer(text, show_alert=True)
        else:
            await target.answer(text)
        return

    await state.set_state(HomeworkAccessState.waiting_sprechen_password)
    await state.update_data(category_id=category_id)

    text = "🔒 <b>Kirish uchun parolni kiriting:</b>"
    keyboard = homework_password_cancel_keyboard()

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.message(HomeworkAccessState.waiting_sprechen_password, F.text)
async def sprechen_password_check(message: Message, state: FSMContext):
    if is_menu_exit(message.text):
        await state.clear()
        await message.answer(
            "🏠 Bosh menyu",
            reply_markup=main_menu_for(message.from_user.id),
        )
        return

    data = await state.get_data()
    category_id = data.get("category_id")

    category = await get_homework_category(category_id) if category_id else None

    if not category:
        await state.clear()
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        return

    if not verify_password(
        message.text.strip(),
        category["password_hash"],
        category["password_salt"],
    ):
        await message.answer(
            "❌ Parol noto'g'ri. Qaytadan urinib ko'ring:",
            reply_markup=homework_password_cancel_keyboard(),
        )
        return

    membership = await get_membership(message.from_user.id, category_id)

    if membership and membership.get("gender") and membership.get("level_group"):
        # Returning member re-authenticating - gender/level_group
        # stay exactly as they were, only the access snapshot moves.
        await set_membership_access_password(
            message.from_user.id, category_id, category["password_hash"]
        )
        await state.clear()

        refreshed = await get_membership(message.from_user.id, category_id)

        await message.answer("✅ Kirish tasdiqlandi.")
        await render_sprechen_menu(message, category_id, message.from_user.id, refreshed)
        return

    # Brand-new registration - gender/level_group were stashed in
    # FSM data by sprechen_level_selected above.
    gender = data.get("gender")
    level_group = data.get("level_group")

    if not gender or not level_group:
        await state.clear()
        await message.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")
        return

    await state.set_state(HomeworkProfileState.waiting_first_name)
    await state.update_data(
        category_id=category_id,
        mode="create",
        gender=gender,
        level_group=level_group,
        sprechen_password_hash=category["password_hash"],
    )

    await message.answer("👤 Ismingizni kiriting:")


@router.message(HomeworkAccessState.waiting_sprechen_password)
async def sprechen_password_invalid_content(message: Message):
    await message.answer(
        "🔒 Parolni matn ko'rinishida kiriting.",
        reply_markup=homework_password_cancel_keyboard(),
    )


# =========================================================
# REGISTRATION - FINISH (called from profile.py's finalize step,
# after first/last name - the existing, unmodified generic steps)
# =========================================================

async def finish_sprechen_registration(
    message: Message,
    category_id: int,
    category_name: str,
    gender: str,
    level_group: str,
    first_name: str,
    last_name: str,
    password_hash: str,
):
    await set_membership_access_password(message.from_user.id, category_id, password_hash)

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
# SERVER-SIDE ACCESS GUARD
# =========================================================
# Re-checked independently by every content handler below (menu,
# lesson select, profile, total score) - not just at the category-
# open entry point - so a deep-link/replayed callback straight to
# e.g. hw:sp:lesson:<id>:<n> can never skip the password check just
# because the corresponding button happened not to be shown.

async def _require_sprechen_access(user_id: int, category_id: int):
    category = await get_homework_category(category_id)
    membership = await get_membership(user_id, category_id)

    if is_sprechen_access_valid(membership, category):
        return category, membership

    return category, None


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

    _, membership = await _require_sprechen_access(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("🔒 Kirish tasdiqlanmagan. Qaytadan kiring.", show_alert=True)
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

    _, membership = await _require_sprechen_access(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("🔒 Kirish tasdiqlanmagan. Qaytadan kiring.", show_alert=True)
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

    _, membership = await _require_sprechen_access(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("🔒 Kirish tasdiqlanmagan. Qaytadan kiring.", show_alert=True)
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

    _, membership = await _require_sprechen_access(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("🔒 Kirish tasdiqlanmagan. Qaytadan kiring.", show_alert=True)
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
