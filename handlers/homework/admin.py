# =========================================================
# HAUSAUFGABEN - ADMIN PANEL
# =========================================================

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.homework import (
    count_homework_users,
    get_category_member_count,
    get_homework_categories,
    get_homework_category,
    get_homework_users,
    set_homework_category_active,
    set_homework_category_password,
)
from database.homework_evaluations import get_evaluation, get_homework_statistics
from database.homework_submissions import count_submissions, get_submission, search_submissions
from keyboards.homework_admin import (
    homework_admin_categories_keyboard,
    homework_admin_category_detail_keyboard,
    homework_admin_home_keyboard,
    homework_admin_submission_detail_keyboard,
    homework_admin_submissions_keyboard,
    homework_admin_users_keyboard,
)
from services.auth import is_admin
from services.homework import is_menu_exit, score_label, status_label
from states.homework import HomeworkAdminState
from utils.security import hash_password

router = Router()

USERS_PAGE_SIZE = 10
SUBS_PAGE_SIZE = 10

ADMIN_HOME_TEXT = "📋 <b>Hausaufgaben - Admin</b>\n\nBo'limni tanlang."


# =========================================================
# HOME
# =========================================================

@router.message(F.text == "📋 Hausaufgaben Admin")
async def homework_admin_home(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        ADMIN_HOME_TEXT,
        parse_mode="HTML",
        reply_markup=homework_admin_home_keyboard(),
    )


@router.callback_query(F.data == "hwa:home")
async def homework_admin_home_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    await callback.message.edit_text(
        ADMIN_HOME_TEXT,
        parse_mode="HTML",
        reply_markup=homework_admin_home_keyboard(),
    )
    await callback.answer()


# =========================================================
# CATEGORIES
# =========================================================

@router.callback_query(F.data == "hwa:cat")
async def homework_admin_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    categories = await get_homework_categories()

    await callback.message.edit_text(
        "📂 <b>Kategoriyalar</b>",
        parse_mode="HTML",
        reply_markup=homework_admin_categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hwa:cat:open:"))
async def homework_admin_category_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    category_id = int(callback.data.split(":")[3])

    category = await get_homework_category(category_id)

    if not category:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return

    member_count = await get_category_member_count(category_id)

    status = "🟢 Faol" if category["is_active"] else "🔴 Faolsiz"
    password_status = "✅ O'rnatilgan" if category["password_hash"] else "❌ O'rnatilmagan"

    text = (
        f"📂 <b>{category['name']}</b>\n\n"
        f"🆔 Kod: <code>{category['code']}</code>\n"
        f"📡 Kanal: <code>{category['channel_id']}</code>\n"
        f"Holat: {status}\n"
        f"🔑 Parol: {password_status}\n"
        f"👥 A'zolar: {member_count}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_admin_category_detail_keyboard(category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hwa:cat:toggle:"))
async def homework_admin_category_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    category_id = int(callback.data.split(":")[3])

    category = await get_homework_category(category_id)

    if not category:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return

    await set_homework_category_active(category_id, not category["is_active"])
    await callback.answer("✅ Holat yangilandi.")

    await homework_admin_category_detail(callback)


@router.callback_query(F.data.startswith("hwa:cat:pwd:"))
async def homework_admin_category_password_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    category_id = int(callback.data.split(":")[3])

    await state.set_state(HomeworkAdminState.waiting_new_password)
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(
        "🔑 Yangi parolni kiriting (kamida 4 ta belgi):"
    )
    await callback.answer()


@router.message(HomeworkAdminState.waiting_new_password, F.text)
async def homework_admin_category_password_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if is_menu_exit(message.text):
        await state.clear()
        return

    password = message.text.strip()

    if len(password) < 4:
        await message.answer("❌ Parol kamida 4 ta belgidan iborat bo'lishi kerak.")
        return

    data = await state.get_data()
    category_id = data.get("category_id")

    category = await get_homework_category(category_id) if category_id else None

    if not category:
        await state.clear()
        await message.answer("❌ Kategoriya topilmadi.")
        return

    password_hash, salt = hash_password(password)
    await set_homework_category_password(category_id, password_hash, salt)

    await state.clear()

    await message.answer(
        f"✅ <b>{category['name']}</b> uchun parol yangilandi.",
        parse_mode="HTML",
        reply_markup=homework_admin_home_keyboard(),
    )


# =========================================================
# USERS
# =========================================================

@router.callback_query(F.data.startswith("hwa:users:"))
async def homework_admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    category_id = int(parts[2]) or None
    page = int(parts[3])

    total = await count_homework_users(category_id)

    users = await get_homework_users(
        category_id, limit=USERS_PAGE_SIZE, offset=page * USERS_PAGE_SIZE
    )

    if not users:
        await callback.message.edit_text(
            "👥 <b>Foydalanuvchilar</b>\n\nHozircha a'zolar mavjud emas.",
            parse_mode="HTML",
            reply_markup=homework_admin_users_keyboard(category_id or 0, 0, False),
        )
        await callback.answer()
        return

    text = f"👥 <b>Foydalanuvchilar</b> (jami: {total})\n\n"

    for u in users:
        text += (
            f"👤 {u['first_name']} {u['last_name']} "
            f"(<code>{u['user_id']}</code>)\n"
            f"📚 {u['category_name']} | 📊 {u['level']} | 📖 {u['lesson_number']}-dars\n"
            f"📤 Vazifalar: {u['submission_count']} | 🏆 Ball: {u['total_score']}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    has_next = (page + 1) * USERS_PAGE_SIZE < total

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_admin_users_keyboard(category_id or 0, page, has_next),
    )
    await callback.answer()


# =========================================================
# SUBMISSIONS
# =========================================================

@router.callback_query(F.data.startswith("hwa:subs:open:"))
async def homework_admin_submission_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    submission_id = int(callback.data.split(":")[3])

    submission = await get_submission(submission_id)

    if not submission:
        await callback.answer("❌ Vazifa topilmadi.", show_alert=True)
        return

    category = await get_homework_category(submission["category_id"])

    score_line = ""
    if submission["status"] not in ("draft", "submitted"):
        evaluation = await get_evaluation(submission_id)
        if evaluation:
            score_line = (
                f"⭐ <b>Ball:</b> {evaluation['score']}/5 - "
                f"{score_label(evaluation['score'])}\n"
            )

    text = (
        f"🆔 <code>{submission['submission_uid']}</code>\n\n"
        f"👤 {submission['first_name']} {submission['last_name']} "
        f"(<code>{submission['user_id']}</code>)\n"
        f"📚 {category['name'] if category else '-'}\n"
        f"📊 {submission['level']} | 📖 {submission['lesson_number']}-dars\n"
        f"{status_label(submission['status'])}\n"
        f"{score_line}"
        f"🕐 {submission['created_at'].strftime('%d.%m.%Y %H:%M')}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_admin_submission_detail_keyboard(submission_id),
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("hwa:subs:") & ~F.data.startswith("hwa:subs:open:")
)
async def homework_admin_submissions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    category_id = int(parts[2]) or None
    page = int(parts[3])

    total = await count_submissions(category_id=category_id)

    submissions = await search_submissions(
        category_id=category_id,
        limit=SUBS_PAGE_SIZE,
        offset=page * SUBS_PAGE_SIZE,
    )

    if not submissions:
        await callback.message.edit_text(
            "📋 <b>Vazifalar</b>\n\nHozircha yuborilgan vazifalar mavjud emas.",
            parse_mode="HTML",
            reply_markup=homework_admin_submissions_keyboard([], category_id or 0, 0, False),
        )
        await callback.answer()
        return

    has_next = (page + 1) * SUBS_PAGE_SIZE < total

    await callback.message.edit_text(
        f"📋 <b>Vazifalar</b> (jami: {total})\n\nBatafsil ko'rish uchun tanlang:",
        parse_mode="HTML",
        reply_markup=homework_admin_submissions_keyboard(
            submissions, category_id or 0, page, has_next
        ),
    )
    await callback.answer()


# =========================================================
# STATISTICS
# =========================================================

@router.callback_query(F.data == "hwa:stats")
async def homework_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    stats = await get_homework_statistics()

    text = (
        "📊 <b>Hausaufgaben Statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n\n"
    )

    for row in stats["by_category"]:
        text += f"{row['category_name']}: <b>{row['member_count']}</b>\n"

    text += (
        f"\n📤 Jami vazifalar: <b>{stats['total_submissions']}</b>\n"
        f"✅ Baholangan: <b>{stats['evaluated_submissions']}</b>\n"
        f"🟡 Kutilmoqda: <b>{stats['pending_submissions']}</b>\n"
        f"🏆 Jami ball: <b>{stats['total_points']}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_admin_home_keyboard(),
    )
    await callback.answer()
