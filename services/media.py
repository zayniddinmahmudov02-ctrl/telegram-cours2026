# =========================================================
# IMPORTS
# =========================================================

from services.loader import BUCHER, FILME, MUSIK

# Root-level movie categories shown in the Medien menu. The
# dict key is matched (case-insensitively) against Filme.csv's
# `category` column; the value is the button/header label.
# Which titles land under each is entirely data-driven - adding
# a Filme.csv row with category=film or category=Zeichentrick
# never requires a code change. Any other/unknown category value
# (e.g. old "serie" rows) is simply excluded from both.
MOVIE_CATEGORIES = {
    "film": "🎥 Film",
    "zeichentrick": "🎬 Zeichentrickfilm",
}


# =========================================================
# HELPERS
# =========================================================

def _casefold(text: str) -> str:
    return text.strip().casefold()


def _matches(title: str, query: str) -> bool:
    return _casefold(query) in _casefold(title)


def _movie_category_key(item: dict) -> str | None:
    key = item["category"].strip().casefold()
    return key if key in MOVIE_CATEGORIES else None


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

def get_movies(category: str) -> list[dict]:
    key = category.strip().casefold()

    return sorted(
        (
            item for item in FILME
            if _movie_category_key(item) == key
        ),
        key=_by_title,
    )


def get_movie_by_message_id(message_id: int) -> dict | None:
    return next(
        (
            item for item in FILME
            if item["message_id"] == message_id
            and _movie_category_key(item) is not None
        ),
        None,
    )


def search_movies(query: str) -> list[dict]:
    return sorted(
        (
            item for item in FILME
            if _movie_category_key(item) is not None
            and _matches(item["title"], query)
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
