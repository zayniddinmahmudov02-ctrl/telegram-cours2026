from config import (
    LEVEL_CONFIG,
    LEVEL_ORDER,
)

from database.certificates import (
    get_level_progress,
    get_all_progress,
)

# =========================================================
# GRADE SYSTEM
# =========================================================

def calculate_rank(
    percent: float,
) -> str:

    if percent >= 90:
        return "🥇 Gold"

    if percent >= 80:
        return "🥈 Silver"

    if percent >= 70:
        return "🥉 Bronze"

    return "🎖 Participant"


# =========================================================
# AVERAGE
# =========================================================

def calculate_average(
    scores: list[int],
    block_size: int,
) -> int:

    if not scores:
        return 0

    percents = []

    for score in scores:

        percents.append(
            round(
                score / block_size * 100
            )
        )

    return round(
        sum(percents)
        / len(percents)
    )


# =========================================================
# LEVEL COMPLETE
# =========================================================

def level_completed(
    scores: list[int],
    block_size: int,
) -> bool:

    for score in scores:

        if score < block_size:
            return False

    return True


# =========================================================
# STARTED
# =========================================================

def level_started(
    scores: list[int],
) -> bool:

    return any(
        score > 0
        for score in scores
    )
# =========================================================
# LEVEL STATUS
# =========================================================

def build_level_status(
    user_id: int,
    level: str,
) -> dict:

    config = LEVEL_CONFIG[level]

    scores = get_level_progress(
        user_id,
        level,
    )

    block_size = config["size"]

    completed_blocks = sum(
        1
        for score in scores
        if score >= block_size
    )

    average = calculate_average(
        scores,
        block_size,
    )

    ready = level_completed(
        scores,
        block_size,
    )

    started = level_started(
        scores,
    )

    return {
        "level": level,
        "ready": ready,
        "started": started,
        "average": average,
        "rank": (
            calculate_rank(average)
            if ready
            else ""
        ),
        "completed_blocks": completed_blocks,
        "remaining_blocks": (
            len(scores)
            - completed_blocks
        ),
        "scores": scores,
    }


# =========================================================
# ALL LEVELS
# =========================================================

def build_all_statuses(
    user_id: int,
) -> list[dict]:

    statuses = []

    for level in LEVEL_ORDER:

        statuses.append(
            build_level_status(
                user_id,
                level,
            )
        )

    return statuses


# =========================================================
# CERTIFICATE READY
# =========================================================

def certificate_ready(
    user_id: int,
    level: str,
) -> bool:

    return build_level_status(
        user_id,
        level,
    )["ready"]


# =========================================================
# STATISTICS
# =========================================================

def certificate_statistics(
    user_id: int,
) -> dict:

    statuses = build_all_statuses(
        user_id,
    )

    ready = sum(
        1
        for status in statuses
        if status["ready"]
    )

    started = sum(
        1
        for status in statuses
        if status["started"]
    )

    return {
        "levels": len(statuses),
        "started": started,
        "ready": ready,
        "remaining": (
            len(statuses)
            - ready
        ),
        "statuses": statuses,
    }