import random

from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_execute
from config import (
    LEVEL_ORDER,
    LEVEL_CONFIG,
    QUIZ_DATA,
    quiz_sessions,
    quiz_running,
    active_questions,
    answered_users,
)

from loader import bot
from logger import logger

# =========================================================
# CHECK LEVEL UNLOCK
# =========================================================

def check_level_unlock(user_id, current_level):

    if current_level == "C1":
        return None

    config = LEVEL_CONFIG.get(current_level)

    if not config:
        return None

    required = config["required"]

    result = db_execute(
        """
        SELECT COALESCE(SUM(best_score),0)
        FROM quiz_progress
        WHERE user_id=%s
        AND level=%s
        """,
        (
            user_id,
            current_level
        ),
        fetchone=True
    )

    total = result[0] if result else 0

    if total >= required:

        try:

            next_level = LEVEL_ORDER[
                LEVEL_ORDER.index(current_level) + 1
            ]

            db_execute(
                """
                UPDATE users
                SET unlocked_level=%s
                WHERE user_id=%s
                """,
                (
                    next_level,
                    user_id
                )
            )

            return next_level

        except (ValueError, IndexError) as e:

            logger.error(
                f"Unlock error: {e}"
            )

            return None

    return None
# =========================================================
# START QUIZ BLOCK
# =========================================================

async def start_quiz_block(
    message: Message,
    level: str,
    block: int,
    force_restart=False,
    user_id=None
):

    if user_id is None:
        user_id = message.from_user.id

    # ACTIVE QUIZ CHECK

    if user_id in quiz_running:

        session = quiz_sessions.get(user_id)

        if not session:

            quiz_running.discard(user_id)

        else:

            await message.answer(
                "⚠️ Sizda hali ham tugallanmagan aktiv test mavjud."
            )

            return

    # USER LEVEL

    user_data = db_execute(
        """
        SELECT unlocked_level
        FROM users
        WHERE user_id=%s
        """,
        (user_id,),
        fetchone=True
    )

    current_unlocked = (
        user_data[0]
        if user_data
        else "A1"
    )

    if (
        level not in LEVEL_ORDER
        or
        current_unlocked not in LEVEL_ORDER
    ):
        await message.answer(
            "❌ Xatolik yuz berdi."
        )
        return

    # BLOCK SECURITY

    config = LEVEL_CONFIG.get(level)

    if (
        not config
        or
        block > config["blocks"]
    ):

        await message.answer(
            "❌ Noto'g'ri blok."
        )

        return
    # =====================================================
    # PREVIOUS BLOCK CHECK
    # =====================================================

    if block > 1 and not force_restart:

        prev_block = block - 1

        res = db_execute(
            """
            SELECT best_score
            FROM quiz_progress
            WHERE user_id = %s
            AND level = %s
            AND block_number = %s
            """,
            (
                user_id,
                level,
                prev_block
            ),
            fetchone=True
        )

        if not res or (res[0] or 0) < 60:

            await message.answer(
                f"🔒 Avval {prev_block}-Blokdan kamida 60/100 ball to'plang."
            )

            return

    # =====================================================
    # LOAD QUESTIONS
    # =====================================================

    questions = QUIZ_DATA.get(level, [])

    start_index = (block - 1) * 100

    end_index = (
        1100
        if level == "C1" and block == 11
        else start_index + 100
    )

    block_questions = questions[start_index:end_index]

    if not block_questions:

        await message.answer(
            "❌ Blokda savollar topilmadi."
        )

        return

    # =====================================================
    # START QUIZ
    # =====================================================

    random.shuffle(block_questions)

    # Oldingi sessiyani tozalash
    quiz_running.discard(user_id)
    quiz_sessions.pop(user_id, None)

    # Eski savollarni tozalash
    keys_to_delete = [
        key
        for key in active_questions
        if key.startswith(f"{user_id}_")
    ]

    for key in keys_to_delete:

        active_questions.pop(key, None)
        answered_users.pop(key, None)

    # Yangi sessiya
    quiz_running.add(user_id)

    quiz_sessions[user_id] = {
        "level": level,
        "block": block,
        "questions": block_questions,
        "index": 0,
        "score": 0,
    }

    await message.answer(
        f"🚀 {level}-{block}-Blok boshlandi!\n"
        f"📚 Savollar soni: {len(block_questions)}"
    )

    await send_next_question(
        message.chat.id,
        user_id
    )

# =========================================================
# SEND NEXT QUESTION
# =========================================================

async def send_next_question(
    chat_id,
    user_id
):

    session = quiz_sessions.get(user_id)

    if not session:

        quiz_running.discard(user_id)

        return

    questions = session["questions"]
    index = session["index"]

    if index >= len(questions):

        await finish_quiz(
            chat_id,
            user_id
        )

        return

    question = questions[index]

    answers = [
        question["correct"],
        question["wrong1"],
        question["wrong2"],
    ]

    random.shuffle(answers)

    qid = f"{user_id}_{question['id']}"

    answered_users[qid] = set()

    builder = InlineKeyboardBuilder()

    callback_map = {}

    for i, ans in enumerate(answers):

        key = f"a{i}"

        callback_map[key] = ans

        builder.button(
            text=ans,
            callback_data=f"quiz:{qid}:{key}"
        )

    builder.button(
        text="⛔ Yakunlash",
        callback_data=f"stopquiz:{user_id}"
    )

    builder.adjust(1)

    active_questions[qid] = {
        "user_id": user_id,
        "question_id": question["id"],
        "correct": question["correct"],
        "answers": callback_map,
    }

    try:

        await bot.send_message(
            chat_id,
            (
                f"📚 {session['level']}-{session['block']}\n"
                f"📊 {index + 1}/{len(questions)}\n\n"
                f"🇩🇪 {question['german']}"
            ),
            reply_markup=builder.as_markup()
        )

    except Exception as e:

        logger.error(
            f"Send question error: {e}"
        )

        quiz_running.discard(user_id)

        quiz_sessions.pop(
            user_id,
            None
        )

        active_questions.pop(
            qid,
            None
        )
# =========================================================
# FINISH QUIZ
# =========================================================

async def finish_quiz(
    chat_id,
    user_id
):

    session = quiz_sessions.get(user_id)

    if not session:
        return

    score = session["score"]
    level = session["level"]
    block = session["block"]
    total = len(session["questions"])

    # =====================================================
    # OLD RESULT
    # =====================================================

    old_result = db_execute(
        """
        SELECT best_score
        FROM quiz_progress
        WHERE user_id = %s
        AND level = %s
        AND block_number = %s
        """,
        (
            user_id,
            level,
            block
        ),
        fetchone=True
    )

    old_score = (
        old_result[0]
        if old_result
        else 0
    )

    xp_gain = max(
        0,
        score - old_score
    )

    # =====================================================
    # SAVE QUIZ RESULT
    # =====================================================

    db_execute(
        """
        INSERT INTO quiz_progress
        (
            user_id,
            level,
            block_number,
            best_score
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        ON CONFLICT
        (
            user_id,
            level,
            block_number
        )
        DO UPDATE
        SET best_score =
        GREATEST(
            quiz_progress.best_score,
            EXCLUDED.best_score
        )
        """,
        (
            user_id,
            level,
            block,
            score
        )
    )

    # =====================================================
    # XP UPDATE
    # =====================================================

    if xp_gain > 0:

        db_execute(
            """
            UPDATE users
            SET
                total_score =
                    COALESCE(total_score,0) + %s,

                daily_score =
                    COALESCE(daily_score,0) + %s

            WHERE user_id = %s
            """,
            (
                xp_gain,
                xp_gain,
                user_id
            )
        )

    # =====================================================
    # LEVEL UNLOCK
    # =====================================================

    new_level = check_level_unlock(
        user_id,
        level
    )

    unlock_text = ""

    if new_level:

        unlock_text = (
            "\n\n"
            f"🔓 Yangi daraja ochildi!\n"
            f"🎯 {new_level}"
        )
    # =====================================================
    # RESULT KEYBOARD
    # =====================================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Qayta ishlash",
                    callback_data=f"restartquiz:{level}:{block}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Menyuga qaytish",
                    callback_data="cancelquiz"
                )
            ]
        ]
    )

    # =====================================================
    # SEND RESULT
    # =====================================================

    await bot.send_message(
        chat_id,
        (
            f"🏁 Test yakunlandi!\n\n"
            f"🇩🇪 Daraja: {level}\n"
            f"📚 Blok: {block}\n\n"
            f"🏆 Natija: {score}/{total}\n"
            f"⭐ XP: +{xp_gain}"
            f"{unlock_text}"
        ),
        reply_markup=keyboard
    )

    # =====================================================
    # CLEAN SESSION
    # =====================================================

    quiz_running.discard(user_id)

    quiz_sessions.pop(
        user_id,
        None
    )

    prefix = f"{user_id}_"

    for key in [
        k
        for k in active_questions
        if k.startswith(prefix)
    ]:

        active_questions.pop(
            key,
            None
        )

        answered_users.pop(
            key,
            None
        )
