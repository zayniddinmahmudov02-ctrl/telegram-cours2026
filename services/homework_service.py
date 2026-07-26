from database import homework


# =========================================================
# CREATE
# =========================================================

def create_submission(
    user_id: int,
    course_type: str,
    level: str,
    lesson: int,
    component: str,
    task_number: int | None = None,
):
    if homework.submission_exists(
        user_id=user_id,
        course_type=course_type,
        level=level,
        lesson=lesson,
        component=component,
        task_number=task_number,
    ):
        return None

    homework.create_submission(
        user_id=user_id,
        course_type=course_type,
        level=level,
        lesson=lesson,
        component=component,
        task_number=task_number,
    )

    submissions = homework.get_lesson_submissions(
        user_id,
        course_type,
        level,
        lesson,
    )

    return submissions[-1]


# =========================================================
# GET
# =========================================================

def get_submission(submission_id: int):
    return homework.get_submission(submission_id)


def get_user_submissions(user_id: int):
    return homework.get_user_submissions(user_id)


def get_lesson(
    user_id: int,
    course_type: str,
    level: str,
    lesson: int,
):
    return homework.get_lesson_submissions(
        user_id,
        course_type,
        level,
        lesson,
    )
from database import homework


# =========================================================
# SUBMIT
# =========================================================

def submit(submission_id: int):
    homework.submit_homework(submission_id)


def approve(
    submission_id: int,
    score: int,
    comment: str,
    teacher_id: int,
):
    homework.approve_submission(
        submission_id,
        score,
        comment,
        teacher_id,
    )


def reject(
    submission_id: int,
    comment: str,
    teacher_id: int,
):
    homework.reject_submission(
        submission_id,
        comment,
        teacher_id,
    )


def delete(submission_id: int):
    homework.delete_submission(submission_id)
from database import homework


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():
    return homework.dashboard_statistics()


def pending():
    return homework.get_pending_submissions()


def checked():
    return homework.get_checked_submissions()


def rejected():
    return homework.get_rejected_submissions()


def drafts():
    return homework.get_draft_submissions()


def last_submission(user_id: int):
    return homework.get_last_submission(user_id)
