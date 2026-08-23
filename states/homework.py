from aiogram.fsm.state import State, StatesGroup


class HomeworkAccessState(StatesGroup):
    # Password entry to unlock a category (Video/Online: asked
    # immediately on category open, before anything else)
    waiting_password = State()

    # Sprechen's password step is intentionally a *different* state
    # from the one above, even though both just wait for a text
    # message - Sprechen asks it AFTER gender+level (or, for a
    # returning member whose access has gone stale, on its own),
    # never at category-open time, so it needs its own FSM data
    # shape (category_id [+ gender/level_group for a brand-new
    # registration]) and its own handler (see handlers.homework.
    # sprechen). Keeping it separate avoids any ambiguity about
    # which handler a given "waiting for password text" state means.
    waiting_sprechen_password = State()


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
