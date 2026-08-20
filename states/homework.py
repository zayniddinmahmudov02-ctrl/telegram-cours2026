from aiogram.fsm.state import State, StatesGroup


class HomeworkAccessState(StatesGroup):
    # Password entry to unlock a category
    waiting_password = State()


class HomeworkProfileState(StatesGroup):
    # First-time profile collection (and later editing - same
    # states, FSM data carries a "mode": "create" | "edit" flag).
    # Level/lesson are NOT part of the permanent category profile -
    # see HomeworkSubmissionState below.
    waiting_first_name = State()
    waiting_last_name = State()


class HomeworkSubmissionState(StatesGroup):
    # Level/lesson belong to the individual submission, asked once
    # per new submission (skipped when resuming an existing draft,
    # which already has them) - then the multi-file upload session.
    waiting_level = State()
    waiting_lesson = State()
    uploading = State()


class HomeworkAdminState(StatesGroup):
    # Admin setting/changing a category's password
    waiting_new_password = State()

    # Admin Panel submissions browser filters (values are stashed
    # in FSM *data*, not state - set_state(None) after saving so
    # the data survives while the "waiting for text" state clears)
    waiting_lesson_filter = State()
    waiting_user_filter = State()
