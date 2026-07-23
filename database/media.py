from .connection import db_execute


# =========================================================
# FILMS
# =========================================================

def get_films():
    return db_execute(
        """
        SELECT *
        FROM films
        ORDER BY id
        """,
        fetchall=True,
    )


def get_film(film_id: int):
    return db_execute(
        """
        SELECT *
        FROM films
        WHERE id=%s
        """,
        (film_id,),
        fetchone=True,
    )


# =========================================================
# BOOKS
# =========================================================

def get_books():
    return db_execute(
        """
        SELECT *
        FROM books
        ORDER BY id
        """,
        fetchall=True,
    )


def get_book(book_id: int):
    return db_execute(
        """
        SELECT *
        FROM books
        WHERE id=%s
        """,
        (book_id,),
        fetchone=True,
    )


# =========================================================
# MUSIC
# =========================================================

def get_music():
    return db_execute(
        """
        SELECT *
        FROM music
        ORDER BY id
        """,
        fetchall=True,
    )


def get_music_item(music_id: int):
    return db_execute(
        """
        SELECT *
        FROM music
        WHERE id=%s
        """,
        (music_id,),
        fetchone=True,
    )


# =========================================================
# VIDEOS
# =========================================================

def get_videos():
    return db_execute(
        """
        SELECT *
        FROM videos
        ORDER BY id
        """,
        fetchall=True,
    )


def get_video(video_id: int):
    return db_execute(
        """
        SELECT *
        FROM videos
        WHERE id=%s
        """,
        (video_id,),
        fetchone=True,
    )


# =========================================================
# SEARCH
# =========================================================

def search_books(keyword: str):
    return db_execute(
        """
        SELECT *
        FROM books
        WHERE LOWER(title) LIKE LOWER(%s)
        ORDER BY title
        """,
        (f"%{keyword}%",),
        fetchall=True,
    )


def search_films(keyword: str):
    return db_execute(
        """
        SELECT *
        FROM films
        WHERE LOWER(title) LIKE LOWER(%s)
        ORDER BY title
        """,
        (f"%{keyword}%",),
        fetchall=True,
    )


def search_music(keyword: str):
    return db_execute(
        """
        SELECT *
        FROM music
        WHERE LOWER(title) LIKE LOWER(%s)
        ORDER BY title
        """,
        (f"%{keyword}%",),
        fetchall=True,
    )


def search_videos(keyword: str):
    return db_execute(
        """
        SELECT *
        FROM videos
        WHERE LOWER(title) LIKE LOWER(%s)
        ORDER BY title
        """,
        (f"%{keyword}%",),
        fetchall=True,
    )