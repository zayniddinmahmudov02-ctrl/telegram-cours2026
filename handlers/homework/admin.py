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
    get_homework_category_by_code,
    get_homework_users,
    set_homework_category_active,
    set_homework_category_password,
)
from database.homework_evaluations import (
    get_evaluation,
    get_homework_statistics,
    get_sprechen_statistics,
)
from database.homework_submissions import count_submissions, get_submission, search_submissions
from keyboards.homework_admin import (
    homework_admin_categories_keyboard,
    homework_admin_category_detail_keyboard,
    homework_admin_home_keyboard,
    homework_admin_sprechen_group_keyboard,
    homework_admin_sprechen_keyboard,
    homework_admin_submission_detail_keyboard,
    homework_admin_submissions_keyboard,
    homework_admin_users_keyboard,
)
from services.auth import is_admin
from services.homework import (
    LEVEL_GROUP_LABELS,
    is_menu_exit,
    parse_lesson_number,
    score_label,
    status_label,
)
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


async def _render_category_detail(callback: CallbackQuery, category_id: int, answer_text: str | None = None):
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
    await callback.answer(answer_text)


@router.callback_query(F.data.startswith("hwa:cat:open:"))
async def homework_admin_category_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    category_id = int(callback.data.split(":")[3])

    await _render_category_detail(callback, category_id)


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

    await _render_category_detail(callback, category_id, answer_text="✅ Holat yangilandi.")


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
            f"📚 {u['category_name']}\n"
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


async def _render_submissions(target, state: FSMContext, category_id: int | None, page: int):
    """
    Shared renderer for the submissions browser, whether reached by
    pagination/category (CallbackQuery) or right after saving a
    lesson/user filter (Message). Filters are read from FSM *data*
    (see states.homework.HomeworkAdminState) and passed straight
    into the existing search_submissions/count_submissions repo
    calls - no separate filtering logic.
    """

    data = await state.get_data()
    lesson = data.get("hwa_lesson")
    user_id_filter = data.get("hwa_user_id")

    total = await count_submissions(
        category_id=category_id,
        lesson_number=lesson,
        user_id=user_id_filter,
    )

    submissions = await search_submissions(
        category_id=category_id,
        lesson_number=lesson,
        user_id=user_id_filter,
        limit=SUBS_PAGE_SIZE,
        offset=page * SUBS_PAGE_SIZE,
    )

    filter_parts = []
    if lesson:
        filter_parts.append(f"📖 {lesson}-dars")
    if user_id_filter:
        filter_parts.append(f"👤 <code>{user_id_filter}</code>")

    filter_line = f"\n🔎 Filter: {', '.join(filter_parts)}" if filter_parts else ""

    if not submissions:
        text = (
            "📋 <b>Vazifalar</b>\n\n"
            "Hozircha mos vazifalar mavjud emas."
            f"{filter_line}"
        )
        keyboard = homework_admin_submissions_keyboard([], category_id or 0, 0, False)
    else:
        has_next = (page + 1) * SUBS_PAGE_SIZE < total
        text = (
            f"📋 <b>Vazifalar</b> (jami: {total}){filter_line}\n\n"
            "Batafsil ko'rish uchun tanlang:"
        )
        keyboard = homework_admin_submissions_keyboard(
            submissions, category_id or 0, page, has_next
        )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await target.answer()
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(
    F.data.startswith("hwa:subs:") & ~F.data.startswith("hwa:subs:open:")
)
async def homework_admin_submissions(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    category_id = int(parts[2]) or None
    page = int(parts[3])

    await _render_submissions(callback, state, category_id, page)


# =========================================================
# SUBMISSIONS - FILTERS (lesson / user / clear)
# =========================================================

@router.callback_query(F.data == "hwa:subsfilter:lesson")
async def homework_admin_subs_filter_lesson_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(HomeworkAdminState.waiting_lesson_filter)

    await callback.message.edit_text("🔎 Dars raqamini kiriting:")
    await callback.answer()


@router.message(HomeworkAdminState.waiting_lesson_filter, F.text)
async def homework_admin_subs_filter_lesson_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if is_menu_exit(message.text):
        await state.clear()
        return

    lesson = parse_lesson_number(message.text)

    if lesson is None:
        await message.answer("❌ Noto'g'ri dars raqami. Masalan: 10")
        return

    await state.update_data(hwa_lesson=lesson)
    await state.set_state(None)

    await _render_submissions(message, state, None, 0)


@router.callback_query(F.data == "hwa:subsfilter:user")
async def homework_admin_subs_filter_user_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    await state.set_state(HomeworkAdminState.waiting_user_filter)

    await callback.message.edit_text("👤 Foydalanuvchining Telegram ID sini kiriting:")
    await callback.answer()


@router.message(HomeworkAdminState.waiting_user_filter, F.text)
async def homework_admin_subs_filter_user_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if is_menu_exit(message.text):
        await state.clear()
        return

    text = message.text.strip()

    if not text.isdigit():
        await message.answer("❌ Noto'g'ri Telegram ID. Faqat raqam kiriting.")
        return

    await state.update_data(hwa_user_id=int(text))
    await state.set_state(None)

    await _render_submissions(message, state, None, 0)


@router.callback_query(F.data == "hwa:subsfilter:clear")
async def homework_admin_subs_filter_clear(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    data = await state.get_data()
    data.pop("hwa_lesson", None)
    data.pop("hwa_user_id", None)
    await state.set_data(data)

    await _render_submissions(callback, state, None, 0)


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


# =========================================================
# SPRECHEN STATISTICS
# =========================================================
# Sprechen's `level` column holds the level_group code (see
# handlers.homework.sprechen / get_sprechen_statistics), so "open a
# group" reuses the existing generic search_submissions(level=...)
# unchanged - no separate Sprechen submissions query needed.

def _format_sprechen_group_stats(label: str, group: dict | None) -> str:
    if not group:
        return f"{label}\nMa'lumot yo'q.\n"

    average = group["average_score"] if group["average_score"] is not None else "-"

    return (
        f"{label}\n"
        f"👥 Ro'yxatdan o'tgan: {group['registered']}\n"
        f"👨 Erkak: {group['male_count']} | 👩 Ayol: {group['female_count']}\n"
        f"📤 Yuborilgan: {group['submitted_count']}\n"
        f"✅ Bajarilgan darslar: {group['completed_count']}\n"
        f"📊 O'rtacha ball: {average}\n"
        f"⭐ Jami ball: {group['total_score']}\n"
    )


@router.callback_query(F.data == "hwa:sp:stats")
async def homework_admin_sprechen_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    category = await get_homework_category_by_code("sprechen")

    if not category:
        await callback.answer("❌ Sprechen kategoriyasi topilmadi.", show_alert=True)
        return

    stats = await get_sprechen_statistics(category["id"])
    overall = stats["overall"]

    text = "🗣 <b>Sprechen Statistikasi</b>\n\n"

    for code, label in LEVEL_GROUP_LABELS.items():
        text += _format_sprechen_group_stats(label, stats["by_group"].get(code))
        text += "━━━━━━━━━━━━━━\n"

    overall_average = overall["average_score"] if overall["average_score"] is not None else "-"

    text += (
        f"\n📊 <b>Umumiy</b>\n"
        f"👥 Jami ro'yxatdan o'tgan: {overall['registered']}\n"
        f"👨 Erkak: {overall['male_count']} | 👩 Ayol: {overall['female_count']}\n"
        f"📤 Jami yuborilgan: {overall['submitted_count']}\n"
        f"✅ Jami bajarilgan darslar: {overall['completed_count']}\n"
        f"📊 O'rtacha ball: {overall_average}\n"
        f"⭐ Jami ball: {overall['total_score']}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_admin_sprechen_keyboard(category["id"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("hwa:sp:group:"))
async def homework_admin_sprechen_group(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    category_id = int(parts[3])
    group_code = parts[4]

    submissions = await search_submissions(
        category_id=category_id, level=group_code, limit=15
    )

    label = LEVEL_GROUP_LABELS.get(group_code, group_code)
    text = f"{label}\n\n📋 <b>Oxirgi vazifalar</b>\n\n"

    if not submissions:
        text += "Hozircha mavjud emas."
    else:
        for s in submissions:
            score_part = f" — {s['score']}/5" if s["score"] is not None else ""
            text += (
                f"👤 {s['first_name']} {s['last_name']} | "
                f"📖 {s['lesson_number']}-dars{score_part}\n"
            )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_admin_sprechen_group_keyboard(),
    )
    await callback.answer()
