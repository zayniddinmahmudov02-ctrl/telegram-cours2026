from aiogram.fsm.state import State, StatesGroup


class HomeworkAccessState(StatesGroup):
    # Password entry to unlock a category
    waiting_password = State()


class HomeworkProfileState(StatesGroup):
    # First-time profile collection (and later editing - same
    # states, FSM data carries a "mode": "create" | "edit" flag)
    waiting_level = State()
    waiting_lesson = State()
    waiting_first_name = State()
    waiting_last_name = State()


class HomeworkSubmissionState(StatesGroup):
    # Multi-file upload session for one draft submission
    uploading = State()


class HomeworkAdminState(StatesGroup):
    # Admin setting/changing a category's password
    waiting_new_password = State()
