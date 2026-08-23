# =========================================================
# HAUSAUFGABEN - ROOT / CATEGORY ACCESS
# =========================================================
# Entry point (main menu button) -> category list -> password
# gate for first-time entry -> category home menu. Everything
# after the main-menu button is inline-keyboard driven (category
# id lives in callback_data), same convention as handlers.media,
# so "which category am I in" never depends on fragile FSM state
# surviving a restart - only the password/profile text steps do.

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.homework import (
    get_active_homework_categories,
    get_homework_category,
    get_membership,
)
from keyboards.homework import (
    homework_categories_keyboard,
    homework_menu_keyboard,
    homework_password_cancel_keyboard,
)
from keyboards.main import main_menu_for
from services.homework import is_menu_exit, is_sprechen_access_valid
from states.homework import HomeworkAccessState
from utils.security import verify_password

router = Router()

ROOT_TEXT = "📚 <b>Hausaufgaben</b>\n\nKategoriyani tanlang."


def category_menu_text(category_name: str) -> str:
    return f"📚 <b>{category_name}</b>\n\nBo'limni tanlang."


# =========================================================
# ENTRY POINT
# =========================================================

@router.message(F.text == "📚 Hausaufgaben")
async def homework_root(message: Message, state: FSMContext):
    await state.clear()

    categories = await get_active_homework_categories()

    if not categories:
        await message.answer(
            "📭 Hozircha Hausaufgaben kategoriyalari mavjud emas."
        )
        return

    await message.answer(
        ROOT_TEXT,
        parse_mode="HTML",
        reply_markup=homework_categories_keyboard(categories),
    )


@router.callback_query(F.data == "hw:root")
async def homework_root_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    categories = await get_active_homework_categories()

    if not categories:
        await callback.message.edit_text(
            "📭 Hozircha Hausaufgaben kategoriyalari mavjud emas."
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        ROOT_TEXT,
        parse_mode="HTML",
        reply_markup=homework_categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(F.data == "hw:noop")
async def homework_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "hw:back_main")
async def homework_back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.edit_text("📚 Hausaufgaben")

    await callback.message.answer(
        "🏠 Bosh menyu",
        reply_markup=main_menu_for(callback.from_user.id),
    )
    await callback.answer()


# =========================================================
# CATEGORY MENU (helper reused by other homework handler
# modules, e.g. after successful password / profile save)
# =========================================================

async def render_category_menu(target, category_id: int, category_name: str):
    text = category_menu_text(category_name)
    keyboard = homework_menu_keyboard(category_id)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=keyboard)


# =========================================================
# OPEN CATEGORY (membership check / password gate)
# =========================================================

@router.callback_query(F.data.startswith("hw:cat:"))
async def homework_open_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[2])

    category = await get_homework_category(category_id)

    if not category or not category["is_active"]:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return

    membership = await get_membership(callback.from_user.id, category_id)

    # Sprechen: a membership row existing is NOT enough - gender,
    # level, and a password snapshot matching the category's
    # CURRENT password must all hold (see services.homework.
    # is_sprechen_access_valid). Anything else (no membership yet,
    # or a stale/rotated password) goes through the dedicated
    # gender -> level -> password flow instead of the generic one
    # below, and NEVER through the generic password-first gate.
    if category["code"] == "sprechen":
        if membership and is_sprechen_access_valid(membership, category):
            from handlers.homework.sprechen import render_sprechen_menu

            await render_sprechen_menu(callback, category_id, callback.from_user.id, membership)
            await callback.answer()
            return

        from handlers.homework.sprechen import start_sprechen_access_flow

        await start_sprechen_access_flow(callback, state, category_id, membership)
        await callback.answer()
        return

    if membership:
        await render_category_menu(callback, category_id, category["name"])
        await callback.answer()
        return

    if not category["password_hash"]:
        await callback.answer(
            "⚠️ Bu kategoriya uchun parol hali sozlanmagan. "
            "Administrator bilan bog'laning.",
            show_alert=True,
        )
        return

    await state.set_state(HomeworkAccessState.waiting_password)
    await state.update_data(category_id=category_id)

    await callback.message.edit_text(
        f"🔒 <b>{category['name']}</b>\n\nKirish uchun parolni kiriting:",
        parse_mode="HTML",
        reply_markup=homework_password_cancel_keyboard(),
    )
    await callback.answer()


# =========================================================
# PASSWORD CHECK
# =========================================================

@router.message(HomeworkAccessState.waiting_password, F.text)
async def homework_password_check(message: Message, state: FSMContext):
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

    # Correct password - hand off to first-time registration rather
    # than granting access here directly, since a membership row is
    # only created once registration is complete. Only Video/Online
    # ever reach this state - Sprechen asks its password later, via
    # its own HomeworkAccessState.waiting_sprechen_password (see
    # handlers.homework.sprechen), never at category-open time.
    from handlers.homework.profile import start_profile_collection

    await start_profile_collection(message, state, category_id, mode="create")


@router.message(HomeworkAccessState.waiting_password)
async def homework_password_invalid_content(message: Message):
    await message.answer(
        "🔒 Parolni matn ko'rinishida kiriting.",
        reply_markup=homework_password_cancel_keyboard(),
    )
