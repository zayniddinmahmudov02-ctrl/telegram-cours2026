from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp

from keyboards import *

from database import *
from teacher_homework import send_homework_to_teacher
from states import HomeworkStates

# =========================================================
# HOMEWORK CONSTANTS
# =========================================================

ONLINE = "online"
VIDEO = "video"
SPEAKING = "speaking"

LEVELS = ["A1", "A2", "B1", "B2", "C1"]

KOMPETENZEN = [
    "Lesen",
    "Hören",
    "Schreiben",
    "Sprechen",
    "Wortschatz"
]# =========================================================
# HOMEWORK CONSTANTS
# =========================================================

ONLINE = "online"
VIDEO = "video"
SPEAKING = "speaking"

LEVELS = ["A1", "A2", "B1", "B2", "C1"]

KOMPETENZEN = [
    "Lesen",
    "Hören",
    "Schreiben",
    "Sprechen",
    "Wortschatz"
]
# =========================================================
# HOMEWORK MENU
# =========================================================

@dp.message_handler(text="📝 Homework")
async def homework_menu_handler(message: types.Message):

    await message.answer(
        "Kategoriyani tanlang.",
        reply_markup=homework_menu
    )
# =========================================================
# CATEGORY
# =========================================================

@dp.message_handler(text="🎓 Online Kurs", state="*")
async def online_category(message: types.Message, state: FSMContext):

    if not has_homework_access(message.from_user.id, ONLINE):
        await message.answer(
            "❌ Sizda Online Homework uchun ruxsat mavjud emas."
        )
        return

    await state.update_data(
        category=ONLINE
    )

    await message.answer(
        "🎓 Online Kurs tanlandi.\n\nKerakli bo'limni tanlang.",
        reply_markup=homework_category_menu
    )


@dp.message_handler(text="🎥 Video Kurs", state="*")
async def video_category(message: types.Message, state: FSMContext):

    if not has_homework_access(message.from_user.id, VIDEO):
        await message.answer(
            "❌ Sizda Video Homework uchun ruxsat mavjud emas."
        )
        return

    await state.update_data(
        category=VIDEO
    )

    await message.answer(
        "🎥 Video Kurs tanlandi.\n\nKerakli bo'limni tanlang.",
        reply_markup=homework_category_menu
    )


@dp.message_handler(text="🗣 Speaking Kurs", state="*")
async def speaking_category(message: types.Message, state: FSMContext):

    if not has_homework_access(message.from_user.id, SPEAKING):
        await message.answer(
            "❌ Sizda Speaking Homework uchun ruxsat mavjud emas."
        )
        return

    await state.update_data(
        category=SPEAKING
    )

    await message.answer(
        "🗣 Speaking Kurs tanlandi.\n\nKerakli bo'limni tanlang.",
        reply_markup=homework_category_menu
    )

# =========================================================
# HOMEWORK ACTION
# =========================================================

@dp.message_handler(text="📝 Vazifa yuborish", state="*")
async def homework_submit(message: types.Message, state: FSMContext):

    data = await state.get_data()

    category = data.get("category")

    if category in [ONLINE, VIDEO]:

        await HomeworkStates.level.set()

        await message.answer(
            "📚 Darajani tanlang.",
            reply_markup=homework_level_menu
        )

        return

    if category == SPEAKING:

        await HomeworkStates.lesson.set()

        await message.answer(
            "🗣 Lessonni tanlang.",
            reply_markup=build_speaking_lesson_menu()
        )

        return


@dp.message_handler(text="💬 Kontakt mit Lehrer", state="*")
async def contact_teacher(message: types.Message, state: FSMContext):

    await HomeworkStates.teacher_question.set()

    await message.answer(
        "✍️ Savolingizni yoki materiallaringizni yuboring.\n\n"
        "Bir nechta fayl yuborishingiz mumkin.\n\n"
        "Tayyor bo'lgach '✅ Ustozga yuborish' tugmasi chiqadi."
    )
# =========================================================
# LEVEL
# =========================================================

@dp.message_handler(state=HomeworkStates.level)
async def select_level(message: types.Message, state: FSMContext):

    level = message.text.replace("🟢 ", "") \
                        .replace("🔵 ", "") \
                        .replace("🟡 ", "") \
                        .replace("🟠 ", "") \
                        .replace("🔴 ", "")

    if level not in LEVELS:
        return

    await state.update_data(level=level)

    await HomeworkStates.lesson.set()

    await message.answer(
        f"📖 {level} darsini tanlang.",
        reply_markup=build_lesson_menu(level)
    )
# =========================================================
# LESSON
# =========================================================

@dp.message_handler(state=HomeworkStates.lesson)
async def select_lesson(message: types.Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("❌ Lesson raqamini tanlang.")
        return

    lesson = int(message.text)

    data = await state.get_data()
    category = data.get("category")

    await state.update_data(
        lesson=lesson
    )

    # ===============================
    # ONLINE / VIDEO
    # ===============================

    if category in [ONLINE, VIDEO]:

        await HomeworkStates.kompetenz.set()

        await message.answer(
            "📚 Kompetenzni tanlang.",
            reply_markup=kompetenz_menu
        )

        return

    # ===============================
    # SPEAKING
    # ===============================

    if category == SPEAKING:

        await HomeworkStates.task_number.set()

        await message.answer(
            "📝 Topshiriq raqamini kiriting.\n\n"
            "Masalan: 3 yoki 12"
        )
# =========================================================
# SPEAKING TASK NUMBER
# =========================================================

@dp.message_handler(state=HomeworkStates.task_number)
async def speaking_task_number(message: types.Message, state: FSMContext):

    task = message.text.strip()

    await state.update_data(
        task_number=task
    )

    await HomeworkStates.upload.set()

    await message.answer(
        "📎 Endi materiallaringizni yuboring.\n\n"
        "Qo'llab-quvvatlanadi:\n"
        "• Photo\n"
        "• Voice\n"
        "• Audio\n"
        "• PDF\n"
        "• Document\n"
        "• Text"
    )
# =========================================================
# FILE UPLOAD
# =========================================================

MAX_FILES = 20


@dp.message_handler(
    content_types=types.ContentTypes.ANY,
    state=HomeworkStates.upload
)
async def upload_files(message: types.Message, state: FSMContext):

    data = await state.get_data()

    files = data.get("files", [])

    # ---------- TEXT ----------

    if message.content_type == "text":

        if message.text == "✅ Ustozga yuborish":

            if not files:

                await message.answer(
                    "❌ Hech qanday material yuborilmadi."
                )
                return

            await HomeworkStates.preview.set()

            await show_preview(
                message,
                state
            )

            return

        files.append({
            "type": "text",
            "text": message.text
        })

    # ---------- PHOTO ----------

    elif message.content_type == "photo":

        files.append({
            "type": "photo",
            "file_id": message.photo[-1].file_id
        })

    # ---------- DOCUMENT ----------

    elif message.content_type == "document":

        files.append({
            "type": "document",
            "file_id": message.document.file_id,
            "name": message.document.file_name
        })

    # ---------- AUDIO ----------

    elif message.content_type == "audio":

        files.append({
            "type": "audio",
            "file_id": message.audio.file_id
        })

    # ---------- VOICE ----------

    elif message.content_type == "voice":

        files.append({
            "type": "voice",
            "file_id": message.voice.file_id
        })

    else:

        await message.answer(
            "❌ Bu format qo'llab-quvvatlanmaydi."
        )
        return

    if len(files) > MAX_FILES:

        await message.answer(
            "❌ Maksimal 20 ta material yuborish mumkin."
        )

        return

    await state.update_data(
        files=files
    )

    await message.answer(
        f"✅ Material qabul qilindi.\n\n"
        f"Jami: {len(files)} ta\n\n"
        f"Tugatgach:\n"
        f"✅ Ustozga yuborish"
    )
# =========================================================
# HOMEWORK PREVIEW
# =========================================================

homework_preview_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Ustozga yuborish")
        ],
        [
            KeyboardButton(text="✏️ Qayta yuklash")
        ],
        [
            KeyboardButton(text="❌ Bekor qilish")
        ]
    ],
    resize_keyboard=True
)
# =========================================================
# SUBMIT
# =========================================================

@dp.message_handler(
    text="✅ Ustozga yuborish",
    state=HomeworkStates.preview
)
async def submit_homework(
    message: types.Message,
    state: FSMContext
):

    data = await state.get_data()

    user_id = message.from_user.id

    category = data["category"]

    level = data.get("level")

    lesson = data.get("lesson")

    kompetenz = data.get("kompetenz")

    task_number = data.get("task_number")

    files = data["files"]

    submission_id = create_homework_submission(

        user_id=user_id,

        category=category,

        level=level,

        lesson=lesson,

        kompetenz=kompetenz,

        task_number=task_number
    )

    for file in files:

        add_homework_file(

            submission_id=submission_id,

            file_type=file["type"],

            file_id=file.get("file_id"),

            text=file.get("text"),

            file_name=file.get("name")
        )

    add_submission_log(

        submission_id,

        "submitted",

        user_id
    )

    await send_homework_to_teacher(
        submission_id,
        state
    )

    await state.finish()

    await message.answer(

        "✅ Homework muvaffaqiyatli yuborildi.\n\n"

        "Ustoz tekshirganidan so'ng sizga baho yuboriladi.",

        reply_markup=main_menu
    )
# =========================================================
# TEACHER RATING
# =========================================================

# =========================================================
# HELPERS
# =========================================================
# =========================================================
# PREVIEW
# =========================================================

async def show_preview(message: types.Message, state: FSMContext):

    data = await state.get_data()

    files = data.get("files", [])

    category = data.get("category")
    level = data.get("level", "-")
    lesson = data.get("lesson", "-")
    kompetenz = data.get("kompetenz", "-")
    task_number = data.get("task_number", "-")

    counts = {
        "photo": 0,
        "voice": 0,
        "audio": 0,
        "document": 0,
        "text": 0
    }

    for file in files:

        file_type = file["type"]

        if file_type in counts:
            counts[file_type] += 1

    text = (
        "📦 <b>Homework Preview</b>\n\n"

        f"📂 Kategoriya: {category}\n"
        f"📚 Level: {level}\n"
        f"📖 Lesson: {lesson}\n"
    )

    if category == SPEAKING:

        text += f"📝 Topshiriq: {task_number}\n"

    else:

        text += f"📖 Kompetenz: {kompetenz}\n"

    text += "\n──────────────\n\n"

    text += (
        f"🖼 Photo: {counts['photo']}\n"
        f"🎤 Voice: {counts['voice']}\n"
        f"🎵 Audio: {counts['audio']}\n"
        f"📄 Document: {counts['document']}\n"
        f"✍ Text: {counts['text']}\n\n"

        f"📦 Jami: {len(files)} ta"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=homework_preview_menu
    )
@dp.callback_query_handler(lambda c: c.data.startswith("hw_rate:"))
async def homework_rating(callback: types.CallbackQuery, state: FSMContext):

    _, submission_id, stars = callback.data.split(":")

    await state.update_data(
        submission_id=int(submission_id),
        stars=int(stars)
    )

    await state.set_state("teacher_feedback")

    await callback.message.answer(

        "✍️ Homework uchun izoh yozing.\n\n"

        "Masalan:\n"

        "Artikel xatolari mavjud.\n"

        "Yoki:\n"

        "Sehr gut!"

    )

    await callback.answer()

@dp.message_handler(state="teacher_feedback")
async def teacher_feedback(message: types.Message, state: FSMContext):

    await state.update_data(
        feedback=message.text
    )

    await state.set_state("teacher_attachment")

    await message.answer(

        "📎 Agar kerak bo'lsa quyidagilarni yuboring:\n\n"

        "• PDF\n"

        "• Photo\n"

        "• Voice\n"

        "• Audio\n\n"

        "Yoki '➡️ O'tkazib yuborish' ni yuboring."
    )

@dp.message_handler(
    content_types=types.ContentTypes.ANY,
    state="teacher_attachment"
)
async def teacher_attachment(message: types.Message, state: FSMContext):

    attachment = None

    if message.text == "➡️ O'tkazib yuborish":

        attachment = None

    elif message.content_type == "photo":

        attachment = {
            "type": "photo",
            "file_id": message.photo[-1].file_id
        }

    elif message.content_type == "voice":

        attachment = {
            "type": "voice",
            "file_id": message.voice.file_id
        }

    elif message.content_type == "audio":

        attachment = {
            "type": "audio",
            "file_id": message.audio.file_id
        }

    elif message.content_type == "document":

        attachment = {
            "type": "document",
            "file_id": message.document.file_id
        }

    else:

        await message.answer("❌ Noto'g'ri format.")
        return

    await state.update_data(
        attachment=attachment
    )

    await state.set_state("teacher_finish")

    await message.answer(
        "Homework natijasini tanlang.",
        reply_markup=teacher_finish_menu
    )
teacher_finish_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton("✅ Qabul qilindi")
        ],
        [
            KeyboardButton("🔄 Qayta topshirish")
        ]
    ],
    resize_keyboard=True
)
@dp.message_handler(state="teacher_finish")
async def finish_homework(message: types.Message, state: FSMContext):

    data = await state.get_data()

    submission_id = data["submission_id"]

    stars = data["stars"]

    feedback = data["feedback"]

    attachment = data.get("attachment")

    if message.text == "✅ Qabul qilindi":
        status = "accepted"

    elif message.text == "🔄 Qayta topshirish":
        status = "revision_required"

    else:
        return

    save_homework_feedback(

        submission_id=submission_id,

        teacher_id=message.from_user.id,

        stars=stars,

        feedback=feedback,

        attachment=attachment,

        status=status

    )

    submission = get_homework_submission(submission_id)

    text = (

        "📚 Homework tekshirildi.\n\n"

        f"⭐ Baho: {stars}/5\n\n"

        f"💬 Izoh:\n{feedback}"
    )

    if status == "accepted":

        text += "\n\n✅ Homework qabul qilindi."

    else:

        text += "\n\n🔄 Homeworkni qayta topshirishingiz kerak."

    await bot.send_message(
        submission["user_id"],
        text
    )

    if attachment:

        if attachment["type"] == "photo":

            await bot.send_photo(
                submission["user_id"],
                attachment["file_id"]
            )

        elif attachment["type"] == "voice":

            await bot.send_voice(
                submission["user_id"],
                attachment["file_id"]
            )

        elif attachment["type"] == "audio":

            await bot.send_audio(
                submission["user_id"],
                attachment["file_id"]
            )

        elif attachment["type"] == "document":

            await bot.send_document(
                submission["user_id"],
                attachment["file_id"]
            )

    await state.finish()

    await message.answer(
        "✅ Natija foydalanuvchiga yuborildi.",
        reply_markup=admin_menu
    )