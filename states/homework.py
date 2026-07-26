from aiogram.fsm.state import State, StatesGroup


# =========================================================
# ONLINE HOMEWORK
# =========================================================

class OnlineHomeworkState(StatesGroup):
    waiting_file = State()


# =========================================================
# VIDEO HOMEWORK
# =========================================================

class VideoHomeworkState(StatesGroup):
    waiting_file = State()


# =========================================================
# SPEAKING HOMEWORK
# =========================================================

class SpeakingHomeworkState(StatesGroup):
    waiting_task = State()
    waiting_file = State()


# =========================================================
# HOMEWORK REVIEW
# =========================================================

class HomeworkReviewState(StatesGroup):
    waiting_comment = State()


# =========================================================
# TEACHER CHAT
# =========================================================

class TeacherChatState(StatesGroup):
    waiting_message = State()
    waiting_file = State()