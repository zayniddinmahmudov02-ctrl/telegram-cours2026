# =========================================================
# HAUSAUFGABEN - PROFILE (first-time collection + later edit)
# =========================================================
# Same 2-step FSM sequence (first name, last name) for both
# "create" and "edit" - FSM data carries a mode flag so the final
# step knows whether to INSERT a new membership or UPDATE the
# existing one. Level/lesson are NOT collected here - they belong
# to the individual submission (see handlers.homework.submission),
# since the same member can submit homework across many different
# levels/lessons without ever re-registering. Editing only touches
# homework_memberships; past submissions keep their own snapshot
# (see database.homework_submissions) so history never changes
# retroactively.

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.homework import (
    create_membership,
    get_homework_category,
    get_membership,
    update_membership_profile,
)
from keyboards.homework import (
    homework_back_to_menu_keyboard,
    homework_profile_keyboard,
)
from keyboards.main import main_menu_for
from services.homework import is_menu_exit, is_valid_name
from states.homework import HomeworkProfileState

router = Router()


# =========================================================
# START
# =========================================================

async def start_profile_collection(
    message: Message,
    state: FSMContext,
    category_id: int,
    mode: str,
):
    await state.set_state(HomeworkProfileState.waiting_first_name)
    await state.update_data(category_id=category_id, mode=mode)

    await message.answer("👤 Ismingizni kiriting:")


@router.callback_query(F.data.startswith("hw:profile:edit:"))
async def homework_profile_edit_start(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[3])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("❌ Avval kategoriyaga a'zo bo'ling.", show_alert=True)
        return

    await state.set_state(HomeworkProfileState.waiting_first_name)
    await state.update_data(category_id=category_id, mode="edit")

    await callback.message.edit_text(
        f"👤 Ismingizni kiriting:\n\n"
        f"Joriy: <b>{membership['first_name']}</b>",
        parse_mode="HTML",
    )
    await callback.answer()


# =========================================================
# EXIT HELPER
# =========================================================

async def _bail_out(message: Message, state: FSMContext) -> bool:
    if not is_menu_exit(message.text):
        return False

    await state.clear()
    await message.answer(
        "🏠 Bosh menyu",
        reply_markup=main_menu_for(message.from_user.id),
    )
    return True


# =========================================================
# FIRST NAME
# =========================================================

@router.message(HomeworkProfileState.waiting_first_name, F.text)
async def homework_profile_first_name(message: Message, state: FSMContext):
    if await _bail_out(message, state):
        return

    first_name = message.text.strip()

    if not is_valid_name(first_name):
        await message.answer("❌ Ism noto'g'ri. Faqat harflardan foydalaning.")
        return

    await state.update_data(first_name=first_name)
    await state.set_state(HomeworkProfileState.waiting_last_name)

    await message.answer("👤 Familiyangizni kiriting:")


# =========================================================
# LAST NAME -> FINALIZE
# =========================================================

@router.message(HomeworkProfileState.waiting_last_name, F.text)
async def homework_profile_last_name(message: Message, state: FSMContext):
    if await _bail_out(message, state):
        return

    last_name = message.text.strip()

    if not is_valid_name(last_name):
        await message.answer("❌ Familiya noto'g'ri. Faqat harflardan foydalaning.")
        return

    data = await state.get_data()
    category_id = data["category_id"]
    mode = data["mode"]
    first_name = data["first_name"]
    gender = data.get("gender")
    level_group = data.get("level_group")
    sprechen_password_hash = data.get("sprechen_password_hash")

    category = await get_homework_category(category_id)

    if not category:
        await state.clear()
        await message.answer("❌ Kategoriya topilmadi.")
        return

    is_sprechen_registration = (
        mode == "create"
        and category["code"] == "sprechen"
        and gender
        and level_group
        and sprechen_password_hash
    )

    if mode == "create":
        await create_membership(
            user_id=message.from_user.id,
            category_id=category_id,
            first_name=first_name,
            last_name=last_name,
            gender=gender if is_sprechen_registration else None,
            level_group=level_group if is_sprechen_registration else None,
        )
    else:
        await update_membership_profile(
            user_id=message.from_user.id,
            category_id=category_id,
            first_name=first_name,
            last_name=last_name,
        )

    await state.clear()

    if is_sprechen_registration:
        from handlers.homework.sprechen import finish_sprechen_registration

        await finish_sprechen_registration(
            message, category_id, category["name"],
            gender, level_group, first_name, last_name,
            sprechen_password_hash,
        )
        return

    from handlers.homework.access import render_category_menu

    if mode == "create":
        await message.answer(
            f"✅ Tabriklaymiz! <b>{category['name']}</b> bo'limiga muvaffaqiyatli qo'shildingiz.",
            parse_mode="HTML",
        )
        await render_category_menu(message, category_id, category["name"])
    else:
        await message.answer(
            "✅ Profil muvaffaqiyatli yangilandi.",
            reply_markup=homework_back_to_menu_keyboard(category_id),
        )


# =========================================================
# VIEW PROFILE
# =========================================================

@router.callback_query(F.data.startswith("hw:profile:") & ~F.data.startswith("hw:profile:edit:"))
async def homework_profile_view(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[2])

    membership = await get_membership(callback.from_user.id, category_id)

    if not membership:
        await callback.answer("❌ Avval kategoriyaga a'zo bo'ling.", show_alert=True)
        return

    category = await get_homework_category(category_id)

    text = (
        "⚙️ <b>Profil</b>\n\n"
        f"👤 <b>Ism:</b> {membership['first_name']}\n"
        f"👤 <b>Familiya:</b> {membership['last_name']}\n"
        f"📚 <b>Kategoriya:</b> {category['name']}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=homework_profile_keyboard(category_id),
    )
    await callback.answer()
