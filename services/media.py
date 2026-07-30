# =========================================================
# IMPORTS
# =========================================================

from services.loader import BUCHER, FILME, MUSIK

# Category values that mark a Filme.csv row as a series
# episode rather than a standalone movie. Serial navigation
# has been removed - these rows are simply excluded.
SERIAL_CATEGORIES = {"serie", "serial", "series"}


# =========================================================
# HELPERS
# =========================================================

def _casefold(text: str) -> str:
    return text.strip().casefold()


def _matches(title: str, query: str) -> bool:
    return _casefold(query) in _casefold(title)


def _is_serial(item: dict) -> bool:
    return item["category"].strip().casefold() in SERIAL_CATEGORIES


def _by_title(item: dict) -> str:
    return item["title"].casefold()


# =========================================================
# BOOKS
# =========================================================

def get_book_levels() -> list[str]:
    return sorted({item["level"] for item in BUCHER})


def get_book_categories(level: str) -> list[str]:
    return sorted({
        item["category"]
        for item in BUCHER
        if item["level"] == level
    })


def get_books(level: str, category: str) -> list[dict]:
    return sorted(
        (
            item for item in BUCHER
            if item["level"] == level
            and item["category"] == category
        ),
        key=_by_title,
    )


def get_book_by_message_id(message_id: int) -> dict | None:
    return next(
        (item for item in BUCHER if item["message_id"] == message_id),
        None,
    )


def search_books(query: str) -> list[dict]:
    return sorted(
        (item for item in BUCHER if _matches(item["title"], query)),
        key=_by_title,
    )


# =========================================================
# MOVIES
# =========================================================

def get_movie_levels() -> list[str]:
    return sorted({
        item["level"] for item in FILME if not _is_serial(item)
    })


def get_movie_categories(level: str) -> list[str]:
    return sorted({
        item["category"]
        for item in FILME
        if item["level"] == level and not _is_serial(item)
    })


def get_movies(level: str, category: str) -> list[dict]:
    return sorted(
        (
            item for item in FILME
            if item["level"] == level
            and item["category"] == category
            and not _is_serial(item)
        ),
        key=_by_title,
    )


def get_movie_by_message_id(message_id: int) -> dict | None:
    return next(
        (
            item for item in FILME
            if item["message_id"] == message_id and not _is_serial(item)
        ),
        None,
    )


def search_movies(query: str) -> list[dict]:
    return sorted(
        (
            item for item in FILME
            if not _is_serial(item) and _matches(item["title"], query)
        ),
        key=_by_title,
    )


# =========================================================
# MUSIC
# =========================================================

def get_music() -> list[dict]:
    return list(MUSIK)


def get_music_by_message_id(message_id: int) -> dict | None:
    return next(
        (item for item in MUSIK if item["message_id"] == message_id),
        None,
    )


def search_music(query: str) -> list[dict]:
    return sorted(
        (item for item in MUSIK if _matches(item["title"], query)),
        key=_by_title,
    )
