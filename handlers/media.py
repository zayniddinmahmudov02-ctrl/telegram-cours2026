# =========================================================
# IMPORTS
# =========================================================

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto,
    Message,
)

from config import (
    BOOK_CHANNEL_ID,
    FILM_CHANNEL_ID,
    MUSIC_CHANNEL_ID,
    MUSIC_COVER_PATH,
)

from services.logger import logger

from services.media import (
    get_book_levels,
    get_book_categories,
    get_books,
    get_book_by_message_id,
    search_books,
    MOVIE_CATEGORIES,
    get_movies,
    get_movie_by_message_id,
    resolve_movie_photo,
    search_movies,
    get_music,
    get_music_by_message_id,
    search_music,
    resolve_music_cover,
    get_favorite_song_list,
)

from database import (
    is_favorite_music,
    toggle_favorite_music,
    remove_favorite_music,
    get_favorite_music_ids,
)

from keyboards.media import (
    media_root_keyboard,
    levels_keyboard,
    categories_keyboard,
    book_list_keyboard,
    movie_gallery_keyboard,
    movie_empty_keyboard,
    music_home_keyboard,
    music_empty_keyboard,
    music_gallery_keyboard,
    music_favorites_empty_keyboard,
    music_favorites_gallery_keyboard,
    search_results_keyboard,
    search_prompt_keyboard,
)

from states.media import MediaSearchState

router = Router()

MEDIA_ROOT_TEXT = "🎬 <b>Media</b>\n\nBo'limni tanlang."


# =========================================================
# SAFE RENDER (text <-> photo aware edit)
# =========================================================
# The movie gallery can land on a photo message (poster found)
# or a text message (no poster / empty category), and users can
# jump between those and any other text screen (root menu,
# search prompt) via the same "⬅️ Orqaga"/nav buttons. Telegram's
# edit_message_text/edit_message_media each only work on their
# own message type, so this always tries the edit that matches
# what's being shown now and falls back to delete+resend if the
# current message turns out to be the other type.

async def _render(
    callback: CallbackQuery,
    keyboard,
    text: str,
    photo_path: str | None = None,
    parse_mode: str | None = None,
    answer_text: str | None = None,
):
    try:
        if photo_path:
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=FSInputFile(photo_path),
                    caption=text,
                ),
                reply_markup=keyboard,
            )
        else:
            await callback.message.edit_text(
                text,
                parse_mode=parse_mode,
                reply_markup=keyboard,
            )

    except TelegramBadRequest:
        await callback.message.delete()

        if photo_path:
            await callback.message.answer_photo(
                FSInputFile(photo_path),
                caption=text,
                reply_markup=keyboard,
            )
        else:
            await callback.message.answer(
                text,
                parse_mode=parse_mode,
                reply_markup=keyboard,
            )

    await callback.answer(answer_text)


# =========================================================
# ROOT
# =========================================================

@router.message(F.text == "🎬 Medien")
async def media_menu(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        MEDIA_ROOT_TEXT,
        parse_mode="HTML",
        reply_markup=media_root_keyboard(),
    )


@router.callback_query(F.data == "media:root")
async def media_root(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await _render(
        callback,
        media_root_keyboard(),
        MEDIA_ROOT_TEXT,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "media:noop")
async def media_noop(callback: CallbackQuery):
    await callback.answer()


# =========================================================
# OPEN HELPER
# =========================================================

async def _open_item(
    callback: CallbackQuery,
    item: dict | None,
    channel_id: int,
    not_found_text: str,
):
    if not item:
        await callback.answer(not_found_text, show_alert=True)
        return

    try:
        await callback.bot.copy_message(
            chat_id=callback.from_user.id,
            from_chat_id=channel_id,
            message_id=item["message_id"],
        )
        await callback.answer()

    except Exception:
        await callback.answer(
            "❌ Post topilmadi yoki o'chirilgan.",
            show_alert=True,
        )


# =========================================================
# BOOKS
# =========================================================

@router.callback_query(F.data == "media:books")
async def books_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    levels = get_book_levels()

    await callback.message.edit_text(
        "📚 <b>Bücher</b>\n\nDarajani tanlang yoki qidiring.",
        parse_mode="HTML",
        reply_markup=levels_keyboard("books", levels),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("media:books:level:"))
async def books_level(callback: CallbackQuery):
    level = callback.data.split(":")[3]

    categories = get_book_categories(level)

    await callback.message.edit_text(
        f"📚 <b>{level}</b>\n\nKategoriyani tanlang.",
        parse_mode="HTML",
        reply_markup=categories_keyboard("books", level, categories),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("media:books:cat:"))
async def books_category(callback: CallbackQuery):
    parts = callback.data.split(":")
    level, category, page = parts[3], parts[4], int(parts[5])

    books = get_books(level, category)

    await callback.message.edit_text(
        f"📚 {level} → {category.capitalize()}\n\nKitobni tanlang.",
        reply_markup=book_list_keyboard(books, page, level, category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("media:books:open:"))
async def books_open(callback: CallbackQuery):
    message_id = int(callback.data.split(":")[3])

    item = get_book_by_message_id(message_id)

    await _open_item(
        callback,
        item,
        BOOK_CHANNEL_ID,
        "❌ Kitob topilmadi.",
    )


@router.callback_query(F.data == "media:books:search")
async def books_search_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MediaSearchState.waiting_book_query)

    await callback.message.edit_text(
        "🔎 Kitob nomini kiriting:",
        reply_markup=search_prompt_keyboard("books"),
    )
    await callback.answer()


@router.message(MediaSearchState.waiting_book_query, F.text)
async def books_search_run(message: Message, state: FSMContext):
    query = message.text.strip()

    if not query:
        await message.answer("🔎 Kitob nomini kiriting:")
        return

    await state.update_data(query=query)

    results = search_books(query)

    if not results:
        await message.answer(
            "❌ Hech narsa topilmadi. Qayta urinib ko'ring.",
            reply_markup=search_prompt_keyboard("books"),
        )
        return

    await message.answer(
        f"🔎 <b>{len(results)} ta natija topildi:</b>",
        parse_mode="HTML",
        reply_markup=search_results_keyboard("books", results, 0),
    )


@router.callback_query(F.data.startswith("media:books:searchpage:"))
async def books_search_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[3])

    data = await state.get_data()
    query = data.get("query")

    if not query:
        await callback.answer(
            "Qidiruv muddati tugadi, qayta qidiring.",
            show_alert=True,
        )
        return

    results = search_books(query)

    await callback.message.edit_text(
        f"🔎 <b>{len(results)} ta natija topildi:</b>",
        parse_mode="HTML",
        reply_markup=search_results_keyboard("books", results, page),
    )
    await callback.answer()


@router.callback_query(F.data == "media:books:cancel_search")
async def books_cancel_search(callback: CallbackQuery, state: FSMContext):
    await books_home(callback, state)


# =========================================================
# MOVIES
# =========================================================
# No level/category picker or list here - the Medien root menu
# links directly to one of the two fixed categories (Film /
# Zeichentrickfilm), and this shows one movie at a time (with
# its poster, if one resolves) with Previous/Next/Watch. Which
# titles exist and their order is resolved dynamically from
# Filme.csv on every call (see services.media) - nothing here is
# hardcoded, so new CSV rows / uploaded posters need no code
# change to show up.

@router.callback_query(F.data.startswith("media:movies:cat:"))
async def movies_category(callback: CallbackQuery):
    parts = callback.data.split(":")
    category, index = parts[3], int(parts[4])

    label = MOVIE_CATEGORIES.get(category, category.capitalize())
    movies = get_movies(category)

    if not movies:
        await _render(
            callback,
            movie_empty_keyboard(),
            f"{label}\n\nHozircha film mavjud emas.",
        )
        return

    index %= len(movies)
    item = movies[index]

    photo_path = resolve_movie_photo(item["photo"])

    if item["photo"] and not photo_path:
        logger.warning(
            f"Movie poster not found: {item['photo']}.* "
            f"(title={item['title']!r})"
        )

    await _render(
        callback,
        movie_gallery_keyboard(
            category,
            index,
            len(movies),
            item["message_id"],
        ),
        item["title"],
        photo_path=photo_path,
    )


@router.callback_query(F.data.startswith("media:movies:open:"))
async def movies_open(callback: CallbackQuery):
    message_id = int(callback.data.split(":")[3])

    item = get_movie_by_message_id(message_id)

    await _open_item(
        callback,
        item,
        FILM_CHANNEL_ID,
        "❌ Film topilmadi.",
    )


@router.callback_query(F.data == "media:movies:search")
async def movies_search_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MediaSearchState.waiting_movie_query)

    await _render(
        callback,
        search_prompt_keyboard("movies"),
        "🔎 Film nomini kiriting:",
    )


@router.message(MediaSearchState.waiting_movie_query, F.text)
async def movies_search_run(message: Message, state: FSMContext):
    query = message.text.strip()

    if not query:
        await message.answer("🔎 Film nomini kiriting:")
        return

    await state.update_data(query=query)

    results = search_movies(query)

    if not results:
        await message.answer(
            "❌ Hech narsa topilmadi. Qayta urinib ko'ring.",
            reply_markup=search_prompt_keyboard("movies"),
        )
        return

    await message.answer(
        f"🔎 <b>{len(results)} ta natija topildi:</b>",
        parse_mode="HTML",
        reply_markup=search_results_keyboard("movies", results, 0),
    )


@router.callback_query(F.data.startswith("media:movies:searchpage:"))
async def movies_search_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[3])

    data = await state.get_data()
    query = data.get("query")

    if not query:
        await callback.answer(
            "Qidiruv muddati tugadi, qayta qidiring.",
            show_alert=True,
        )
        return

    results = search_movies(query)

    await callback.message.edit_text(
        f"🔎 <b>{len(results)} ta natija topildi:</b>",
        parse_mode="HTML",
        reply_markup=search_results_keyboard("movies", results, page),
    )
    await callback.answer()


@router.callback_query(F.data == "media:movies:cancel_search")
async def movies_cancel_search(callback: CallbackQuery, state: FSMContext):
    await media_root(callback, state)


# =========================================================
# MUSIC
# =========================================================
# Home menu (Favorites / Songs / Search) fans out into a
# one-song-at-a-time gallery, mirroring the movie gallery's
# index-based Prev/Next but sharing a single cover image
# (MUSIC_COVER_PATH) across every song instead of per-item
# posters. Which songs exist is resolved dynamically from
# Musik.csv (see services.media) on every call, same as movies.

def _music_caption(title: str) -> str:
    return f"🎵 {title}\n\n🇩🇪 Learn German through music."


@router.callback_query(F.data == "media:music")
async def music_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await _render(
        callback,
        music_home_keyboard(),
        "🎵 <b>Musik</b>\n\nBo'limni tanlang.",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("media:music:songs:"))
async def music_songs(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    songs = get_music()

    if not songs:
        await _render(
            callback,
            music_empty_keyboard(),
            "🎼 <b>Musik</b>\n\nHozircha qo'shiq mavjud emas.",
            parse_mode="HTML",
        )
        return

    index = int(callback.data.split(":")[3]) % len(songs)
    item = songs[index]

    cover_path = resolve_music_cover()

    if not cover_path:
        logger.warning(f"Music cover not found: {MUSIC_COVER_PATH}")

    is_fav = await is_favorite_music(
        callback.from_user.id,
        item["message_id"],
    )

    await _render(
        callback,
        music_gallery_keyboard(
            index,
            len(songs),
            item["message_id"],
            is_fav,
        ),
        _music_caption(item["title"]),
        photo_path=cover_path,
    )


@router.callback_query(F.data.startswith("media:music:fav:"))
async def music_fav_toggle(callback: CallbackQuery):
    index = int(callback.data.split(":")[3])

    songs = get_music()

    if not songs:
        await callback.answer()
        return

    index %= len(songs)
    item = songs[index]

    now_favorite = await toggle_favorite_music(
        callback.from_user.id,
        item["message_id"],
    )

    cover_path = resolve_music_cover()

    if not cover_path:
        logger.warning(f"Music cover not found: {MUSIC_COVER_PATH}")

    await _render(
        callback,
        music_gallery_keyboard(
            index,
            len(songs),
            item["message_id"],
            now_favorite,
        ),
        _music_caption(item["title"]),
        photo_path=cover_path,
        answer_text=(
            "❤️ Sevimlilarga qo'shildi."
            if now_favorite
            else "💔 Sevimlilardan o'chirildi."
        ),
    )


@router.callback_query(F.data.startswith("media:music:favs:"))
async def music_favs(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    telegram_id = callback.from_user.id
    favorite_ids = await get_favorite_music_ids(telegram_id)
    songs = get_favorite_song_list(favorite_ids)

    if not songs:
        await _render(
            callback,
            music_favorites_empty_keyboard(),
            "⭐ <b>Favorites</b>\n\nHozircha sevimli qo'shiqlar yo'q.",
            parse_mode="HTML",
        )
        return

    index = int(callback.data.split(":")[3]) % len(songs)
    item = songs[index]

    cover_path = resolve_music_cover()

    if not cover_path:
        logger.warning(f"Music cover not found: {MUSIC_COVER_PATH}")

    await _render(
        callback,
        music_favorites_gallery_keyboard(
            index,
            len(songs),
            item["message_id"],
        ),
        _music_caption(item["title"]),
        photo_path=cover_path,
    )


@router.callback_query(F.data.startswith("media:music:favremove:"))
async def music_fav_remove(callback: CallbackQuery):
    index = int(callback.data.split(":")[3])

    telegram_id = callback.from_user.id
    favorite_ids = await get_favorite_music_ids(telegram_id)
    songs = get_favorite_song_list(favorite_ids)

    if not songs:
        await _render(
            callback,
            music_favorites_empty_keyboard(),
            "⭐ <b>Favorites</b>\n\nHozircha sevimli qo'shiqlar yo'q.",
            parse_mode="HTML",
        )
        return

    index %= len(songs)
    removed_item = songs[index]

    await remove_favorite_music(telegram_id, removed_item["message_id"])
    songs.pop(index)

    if not songs:
        await _render(
            callback,
            music_favorites_empty_keyboard(),
            "⭐ <b>Favorites</b>\n\nHozircha sevimli qo'shiqlar yo'q.",
            parse_mode="HTML",
            answer_text="💔 Sevimlilardan o'chirildi.",
        )
        return

    index %= len(songs)
    item = songs[index]

    cover_path = resolve_music_cover()

    if not cover_path:
        logger.warning(f"Music cover not found: {MUSIC_COVER_PATH}")

    await _render(
        callback,
        music_favorites_gallery_keyboard(
            index,
            len(songs),
            item["message_id"],
        ),
        _music_caption(item["title"]),
        photo_path=cover_path,
        answer_text="💔 Sevimlilardan o'chirildi.",
    )


@router.callback_query(F.data.startswith("media:music:open:"))
async def music_open(callback: CallbackQuery):
    message_id = int(callback.data.split(":")[3])

    item = get_music_by_message_id(message_id)

    await _open_item(
        callback,
        item,
        MUSIC_CHANNEL_ID,
        "❌ Qo'shiq topilmadi.",
    )


@router.callback_query(F.data == "media:music:search")
async def music_search_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MediaSearchState.waiting_music_query)

    await _render(
        callback,
        search_prompt_keyboard("music"),
        "🔎 Qo'shiq nomini kiriting:",
    )


@router.message(MediaSearchState.waiting_music_query, F.text)
async def music_search_run(message: Message, state: FSMContext):
    query = message.text.strip()

    if not query:
        await message.answer("🔎 Qo'shiq nomini kiriting:")
        return

    await state.update_data(query=query)

    results = search_music(query)

    if not results:
        await message.answer(
            "❌ Hech narsa topilmadi. Qayta urinib ko'ring.",
            reply_markup=search_prompt_keyboard("music"),
        )
        return

    await message.answer(
        f"🔎 <b>{len(results)} ta natija topildi:</b>",
        parse_mode="HTML",
        reply_markup=search_results_keyboard("music", results, 0),
    )


@router.callback_query(F.data.startswith("media:music:searchpage:"))
async def music_search_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[3])

    data = await state.get_data()
    query = data.get("query")

    if not query:
        await callback.answer(
            "Qidiruv muddati tugadi, qayta qidiring.",
            show_alert=True,
        )
        return

    results = search_music(query)

    await callback.message.edit_text(
        f"🔎 <b>{len(results)} ta natija topildi:</b>",
        parse_mode="HTML",
        reply_markup=search_results_keyboard("music", results, page),
    )
    await callback.answer()


@router.callback_query(F.data == "media:music:cancel_search")
async def music_cancel_search(callback: CallbackQuery, state: FSMContext):
    await music_home(callback, state)
