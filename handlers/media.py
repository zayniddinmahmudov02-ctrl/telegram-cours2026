from aiogram import F
from aiogram.types import *
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import os
import csv
import glob
import random
import logging

from bot import dp, bot
from database import *
from keyboards import *
from config import *

# =========================================================
# Medien Handler
# =========================================================

@dp.message(F.text == "🎬 Medien")
async def open_medien(message: Message):

    await message.answer(
        "🎬 Medien bo'limi",
        reply_markup=medien_menu
    )

# =========================================================
# SEARCH STATES
# =========================================================

class SearchState(StatesGroup):

    waiting_query = State()

# =========================================================
# OPEN SEARCH
# =========================================================

@dp.message(
    F.text == "🔍 Qidiruv"
)
async def open_search(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        SearchState.waiting_query
    )

    await message.answer(

        "🔍 Qidiruv\n\n"
        "Kitob, musiqa yoki film nomini yuboring."

    )
# =========================================================
# GLOBAL SEARCH
# =========================================================
@dp.message(
    SearchState.waiting_query
)
async def search_media(
    message: Message,
    state: FSMContext
):
    if not message.text:
        return

    query = (
        message.text
        .lower()
        .strip()
    )

    builder = InlineKeyboardBuilder()

    found = 0

    try:

        # ======================
        # BOOKS
        # ======================

        for book in book_files:

            title = book.get(
                "title",
                ""
            )

            if query in title.lower():

                found += 1

                builder.row(

                    InlineKeyboardButton(

                        text=f"📚 {title}",

                        callback_data=
                        f"bookfile_{book['message_id']}"

                    )

                )

        # ======================
        # MUSIC
        # ======================

        for track_number in music_titles:

            title = music_titles[
                track_number
            ]

            if query in title.lower():

                found += 1

                builder.row(

                    InlineKeyboardButton(

                        text=f"🎵 {title}",

                        callback_data=
                        f"music_{track_number}"

                    )

                )

        await state.clear()

        if found == 0:

            await message.answer(
                "❌ Hech narsa topilmadi."
            )

            return

        await message.answer(

            f"🔍 Topildi: {found}",

            reply_markup=
            builder.as_markup()

        )

    except Exception as e:

        logger.error(
            f"SEARCH ERROR: {e}"
        )

        await state.clear()

        await message.answer(
            "❌ Qidiruvda xatolik."
        )
# =========================================================
# MEDIEN
# =========================================================

MUSIC_CHANNEL_ID = -1003763602068

music_tracks = {}
music_titles = {}

try:

    with open(
        "Musik.csv",
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            track_number = int(
                row["track_number"]
            )

            music_tracks[
                track_number
            ] = int(
                row["message_id"]
            )

            music_titles[
                track_number
            ] = row.get(
                "title",
                f"Track {track_number}"
            )

except Exception as e:

    logger.error(
        f"MUSIK CSV ERROR: {e}"
    )

TOTAL_TRACKS = len(
    music_tracks
)

# =========================================================
# MUSIC KEYBOARD
# =========================================================
def build_music_keyboard(
page=1
):
    builder = InlineKeyboardBuilder()

    tracks = sorted(
        music_titles.keys()
    )

    start_index = (
        page - 1
    ) * 5

    end_index = min(
        start_index + 5,
        len(tracks)
    )

    current_tracks = tracks[
        start_index:end_index
    ]

    for track in current_tracks:

        title = music_titles.get(
            track,
            f"Track {track}"
        )

        builder.row(

            InlineKeyboardButton(

                text=f"{track}. {title[:40]}",

                callback_data=
                f"music_{track}"

            )

        )

    navigation = []

    if page > 1:

        navigation.append(

            InlineKeyboardButton(

                text="⬅️",

                callback_data=
                f"music_page_{page-1}"

            )

        )

    if end_index < len(tracks):

        navigation.append(

            InlineKeyboardButton(

                text="➡️",

                callback_data=
                f"music_page_{page+1}"

            )

        )

    if navigation:

        builder.row(*navigation)

    return builder.as_markup()
# =========================================================
# DE-MUSIK
# =========================================================

@dp.message(
    F.text == "🎵 De-Musik"
)
async def open_music(
    message: Message
):

    if not music_tracks:

        await message.answer(
            "❌ Musik.csv topilmadi."
        )

        return

    await message.answer(
        f"🎵 Deutsche Musik\n\n"
        f"🎼 Jami qo'shiqlar: {TOTAL_TRACKS}\n\n"
        f"Kerakli qo'shiqni tanlang:",
        reply_markup=build_music_keyboard(1)
    )

# =========================================================
# MUSIC PAGE
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "music_page_"
    )
)
async def music_page_handler(
    callback: CallbackQuery
):

    page = int(
        callback.data.split("_")[-1]
    )

    await callback.message.edit_reply_markup(
        reply_markup=
        build_music_keyboard(page)
    )

    await callback.answer()

# =========================================================
# SEND MUSIC
# =========================================================

@dp.callback_query(
    F.data.startswith(
        "music_"
    )
)
async def send_music(
    callback: CallbackQuery
):

    if callback.data.startswith(
        "music_page_"
    ):
        return

    track_number = int(
        callback.data.split("_")[1]
    )

    message_id = music_tracks.get(
        track_number
    )

    if not message_id:

        await callback.answer(
            "❌ Qo'shiq topilmadi",
            show_alert=True
        )

        return

    try:

        await bot.copy_message(
            chat_id=
            callback.from_user.id,

            from_chat_id=
            MUSIC_CHANNEL_ID,

            message_id=
            message_id
        )
        await callback.answer(
    f"🎵 {music_titles.get(track_number, f'Track #{track_number}')}"
)

    except Exception as e:

        logger.error(
            f"MUSIC ERROR: {e}"
        )

        await callback.answer(
            "❌ Audio yuborishda xatolik",
            show_alert=True
        )
# =========================================================
# BOOKS
# =========================================================

BOOK_CHANNEL_ID = -1003796668138

book_files = []

try:
    with open(
        "Bucher.csv",
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            book_files.append({
                "level": row["level"],
                "category": row["category"],
                "title": row["title"],
                "message_id": int(row["message_id"])
            })

except Exception as e:

    logger.error(
        f"BUCHER CSV ERROR: {e}"
    )

TOTAL_BOOKS = len(book_files)
# =========================================================
# BOOK LEVEL MENU
# =========================================================

def build_books_levels():

    builder = InlineKeyboardBuilder()

    levels = [
        "A1",
        "A2",
        "B1",
        "B2",
        "C1"
    ]

    for level in levels:

        builder.row(
            InlineKeyboardButton(
                text=f"🇩🇪 {level}",
                callback_data=f"book_{level}"
            )
        )

    return builder.as_markup()
# =========================================================
# BOOK CATEGORY MENU
# =========================================================

def build_book_categories(level):

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📖 Literarisch",
            callback_data=f"book_{level}_literatur"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📝 Zur Vorbereitung",
            callback_data=f"book_{level}_vorbereitung"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📚 Wortliste",
            callback_data=f"book_{level}_wortliste"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="book_back_levels"
        )
    )

    return builder.as_markup()
# =========================================================
# DE-BUCHER
# =========================================================

@dp.message(F.text == "📚 De-Bücher")
async def open_books(message: Message):

    await message.answer(

        "📚 Deutsche Bücher\n\n"
        "Darajani tanlang:",

        reply_markup=
        build_books_levels()

    )
# =========================================================
# BOOK LEVEL HANDLER
# =========================================================

@dp.callback_query(
    F.data.in_(
        [
            "book_A1",
            "book_A2",
            "book_B1",
            "book_B2",
            "book_C1"
        ]
    )
)
async def book_level_handler(
    callback: CallbackQuery
):

    level = callback.data.split("_")[1]

    await callback.message.edit_text(

        f"📚 {level} Bücher\n\n"
        "Kategoriyani tanlang:",

        reply_markup=
        build_book_categories(level)

    )

    await callback.answer()
# =========================================================
# BACK TO LEVELS
# =========================================================

@dp.callback_query(
    F.data == "book_back_levels"
)
async def back_book_levels(
    callback: CallbackQuery
):

    await callback.message.edit_text(

        "📚 Deutsche Bücher\n\n"
        "Darajani tanlang:",

        reply_markup=
        build_books_levels()

    )

    await callback.answer()
# =========================================================
# BOOK CATEGORY HANDLER
# =========================================================
@dp.callback_query(
    F.data.regexp(
        r"^book_(A1|A2|B1|B2|C1)_(literatur|vorbereitung|wortliste)$"
    )
)
async def book_category_handler(
    callback: CallbackQuery
):
    level = callback.data.split("_")[1]
    category = callback.data.split("_")[2]

    builder = InlineKeyboardBuilder()

    filtered_books = []

    for book in book_files:

        if (
            book["level"] == level
            and
            book["category"] == category
        ):

            filtered_books.append(book)

    if not filtered_books:

        await callback.answer(
            "❌ Kitob topilmadi",
            show_alert=True
        )

        return

    for book in filtered_books:

        builder.row(

            InlineKeyboardButton(

                text=book["title"],

                callback_data=
                f"bookfile_{book['message_id']}"

            )

        )

    await callback.message.edit_text(

        f"📚 {level} | {category}",

        reply_markup=
        builder.as_markup()

    )

    await callback.answer()


# =========================================================
# SEND BOOK FILE
# =========================================================
@dp.callback_query(
    F.data.startswith("bookfile_")
)
async def send_book_file(
    callback: CallbackQuery
):
    message_id = int(
        callback.data.split("_")[1]
    )

    selected_book = None

    for book in book_files:

        if (
            book["message_id"]
            ==
            message_id
        ):

            selected_book = book

            break

    if not selected_book:

        await callback.answer(
            "❌ Kitob topilmadi",
            show_alert=True
        )

        return

    try:

        await bot.copy_message(

            chat_id=
            callback.from_user.id,

            from_chat_id=
            BOOK_CHANNEL_ID,

            message_id=
            selected_book["message_id"]

        )

        await callback.answer(
            "📚 Kitob yuborildi"
        )

    except Exception as e:

        logger.error(
            f"BOOK ERROR: {e}"
        )

        await callback.answer(
            "❌ Kitob yuborishda xatolik",
            show_alert=True
        )

# =========================================================
# DE-FILME
# =========================================================
@dp.message(F.text == "🎬 De-Filme")
async def open_films(message: Message):

    await message.answer(
        "🎬 DE-FILME\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=films_menu
    )


# =========================================================
# A1-A2 FILMS
# =========================================================
@dp.message(
    F.text == "🟢 A1-A2 Filmlari"
)
async def a1_films(
    message: Message
):

    films = [
        x
        for x in FILME
        if x["level"] == "A1"
    ]

    if not films:

        await message.answer(
            "🚧 Hozircha A1-A2 filmlari yuklanmagan."
        )

        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎬 Extra auf Deutsch",
                    callback_data=
                    "extra_deutsch"
                )
            ]
        ]
    )

    await message.answer(
        "🟢 A1-A2 FILMLARI\n\n"
        "Filmni tanlang:",
        reply_markup=kb
    )


# =========================================================
# EXTRA AUF DEUTSCH
# =========================================================
@dp.callback_query(
    F.data == "extra_deutsch"
)
async def extra_deutsch(
    callback: CallbackQuery
):

    films = [
        x
        for x in FILME
        if (
            x["level"] == "A1"
            and
            "Extra auf Deutsch"
            in x["title"]
        )
    ]

    keyboard = []

    for film in films:

        folge = (
            film["title"]
            .split("Folge ")[1]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=folge,
                    callback_data=
                    f"film:{film['message_id']}"
                )
            ]
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

    await callback.message.edit_text(
        "🎬 Extra auf Deutsch\n\n"
        "Folgeni tanlang:",
        reply_markup=kb
    )

    await callback.answer()


# =========================================================
# B1-B2 FILMS
# =========================================================
@dp.message(
    F.text == "🔵 B1-B2 Filmlari"
)
async def b1_films(
    message: Message
):

    films = [
        x
        for x in FILME
        if x["level"] == "B1"
    ]

    if not films:

        await message.answer(
            "🚧 Hozircha B1-B2 filmlari yuklanmagan."
        )

        return

    await message.answer(
        "🔵 B1-B2 FILMLARI\n\n"
        "🚧 Hozircha yuklanmoqda."
    )


# =========================================================
# C1 FILMS
# =========================================================
@dp.message(
    F.text == "🔴 C1 Filmlari"
)
async def c1_films(
    message: Message
):

    films = [
        x
        for x in FILME
        if x["level"] == "C1"
    ]

    if not films:

        await message.answer(
            "🚧 Hozircha C1 filmlari yuklanmagan."
        )

        return

    await message.answer(
        "🔴 C1 FILMLARI\n\n"
        "🚧 Hozircha yuklanmoqda."
    )


# =========================================================
# POPULAR FILMS
# =========================================================
@dp.message(
    F.text == "🌟 Ommaviy Filmlar"
)
async def popular_films(
    message: Message
):

    films = [
        x
        for x in FILME
        if x["level"] == "POPULAR"
    ]

    if not films:

        await message.answer(
            "🚧 Hozircha ommaviy filmlar yuklanmagan."
        )

        return

    keyboard = []

    for film in films:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=
                    f"🎬 {film['title']}",
                    callback_data=
                    f"film:{film['message_id']}"
                )
            ]
        )

    kb = InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

    await message.answer(
        "🌟 OMMAVIY FILMLAR\n\n"
        "Filmni tanlang:",
        reply_markup=kb
    )


# =========================================================
# SEND FILM
# =========================================================
@dp.callback_query(
    F.data.startswith("film:")
)
async def send_film(
    callback: CallbackQuery
):

    try:

        _, message_id = (
            callback.data.split(":")
        )

        await bot.copy_message(
            chat_id=
            callback.from_user.id,

            from_chat_id=
            FILM_CHANNEL_ID,

            message_id=
            int(message_id)
        )

        await callback.answer(
            "🎬 Film yuborildi."
        )

    except Exception as e:

        import traceback
        traceback.print_exc()

        print(
            f"FILM ERROR: {e}"
        )

        await callback.answer(
            "❌ Film topilmadi.",
            show_alert=True
        )


# =========================================================
# BACK TO MEDIEN
# =========================================================
@dp.message(
    F.text == "⬅️ Medien"
)
async def back_medien(
    message: Message
):

    await message.answer(
        "🎬 Medien bo'limi",
        reply_markup=medien_menu
    )
# =========================================================
# BACK FROM MEDIEN
# =========================================================

@dp.message(F.text == "⬅️ Orqaga")
async def back_to_main_menu(
    message: Message
):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu
    )