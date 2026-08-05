from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

PAGE_SIZE = 8

SEARCH_LABELS = {
    "books": "🔎 Kitob qidirish",
    "movies": "🔎 Film qidirish",
    "music": "🔎 Qo'shiq qidirish",
}


# =========================================================
# ROOT
# =========================================================

def media_root_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Bücher",
                    callback_data="media:books",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎥 Film",
                    callback_data="media:movies:cat:film:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎬 Zeichentrickfilm",
                    callback_data="media:movies:cat:zeichentrick:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 Musik",
                    callback_data="media:music",
                )
            ],
        ]
    )


# =========================================================
# LEVELS (books / movies)
# =========================================================

def levels_keyboard(kind: str, levels: list[str]) -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                text=level,
                callback_data=f"media:{kind}:level:{level}",
            )
        ]
        for level in levels
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text=SEARCH_LABELS[kind],
                callback_data=f"media:{kind}:search",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="media:root",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


# =========================================================
# CATEGORIES (books / movies)
# =========================================================

def categories_keyboard(
    kind: str,
    level: str,
    categories: list[str],
) -> InlineKeyboardMarkup:

    rows = [
        [
            InlineKeyboardButton(
                text=category.capitalize(),
                callback_data=f"media:{kind}:cat:{level}:{category}:0",
            )
        ]
        for category in categories
    ]

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data=f"media:{kind}",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


# =========================================================
# PAGINATED ITEM LIST (books / movies / music / search)
# =========================================================

def _items_page_keyboard(
    items: list[dict],
    page: int,
    open_prefix: str,
    page_prefix: str,
    back_callback: str,
    extra_rows: list[list[InlineKeyboardButton]] | None = None,
) -> InlineKeyboardMarkup:

    start = page * PAGE_SIZE
    page_items = items[start:start + PAGE_SIZE]

    rows = [
        [
            InlineKeyboardButton(
                text=item["title"][:60],
                callback_data=f"{open_prefix}{item['message_id']}",
            )
        ]
        for item in page_items
    ]

    total_pages = max(1, -(-len(items) // PAGE_SIZE))

    if total_pages > 1:

        nav_row = []

        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"{page_prefix}:{page - 1}",
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                text=f"{page + 1}/{total_pages}",
                callback_data="media:noop",
            )
        )

        if start + PAGE_SIZE < len(items):
            nav_row.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"{page_prefix}:{page + 1}",
                )
            )

        rows.append(nav_row)

    if extra_rows:
        rows.extend(extra_rows)

    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data=back_callback,
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def book_list_keyboard(
    items: list[dict],
    page: int,
    level: str,
    category: str,
) -> InlineKeyboardMarkup:

    return _items_page_keyboard(
        items,
        page,
        open_prefix="media:books:open:",
        page_prefix=f"media:books:cat:{level}:{category}",
        back_callback=f"media:books:level:{level}",
    )


# =========================================================
# MOVIE GALLERY (one movie at a time, with a poster)
# =========================================================

def movie_gallery_keyboard(
    category: str,
    index: int,
    total: int,
    message_id: int,
) -> InlineKeyboardMarkup:

    if total > 1:
        prev_callback = f"media:movies:cat:{category}:{(index - 1) % total}"
        next_callback = f"media:movies:cat:{category}:{(index + 1) % total}"
    else:
        # Nothing to page through - Prev/Next are no-ops rather
        # than re-rendering the same movie.
        prev_callback = "media:noop"
        next_callback = "media:noop"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Previous",
                    callback_data=prev_callback,
                ),
                InlineKeyboardButton(
                    text="🎥 Watch Movie",
                    callback_data=f"media:movies:open:{message_id}",
                ),
                InlineKeyboardButton(
                    text="➡️ Next",
                    callback_data=next_callback,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=SEARCH_LABELS["movies"],
                    callback_data="media:movies:search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="media:root",
                )
            ],
        ]
    )


def movie_empty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=SEARCH_LABELS["movies"],
                    callback_data="media:movies:search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="media:root",
                )
            ],
        ]
    )


# =========================================================
# MUSIC (home menu + one-song-at-a-time gallery, with a shared
# cover image and personal favorites)
# =========================================================

def music_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Favorites",
                    callback_data="media:music:favs:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎼 Songs",
                    callback_data="media:music:songs:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Search",
                    callback_data="media:music:search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="media:root",
                )
            ],
        ]
    )


def music_empty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Search",
                    callback_data="media:music:search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="media:music",
                )
            ],
        ]
    )


def music_gallery_keyboard(
    index: int,
    total: int,
    message_id: int,
    is_favorite: bool,
) -> InlineKeyboardMarkup:

    if total > 1:
        prev_callback = f"media:music:songs:{(index - 1) % total}"
        next_callback = f"media:music:songs:{(index + 1) % total}"
    else:
        # Nothing to page through - Prev/Next are no-ops rather
        # than re-rendering the same song.
        prev_callback = "media:noop"
        next_callback = "media:noop"

    fav_text = (
        "💔 Remove from Favorites"
        if is_favorite
        else "❤️ Add to Favorites"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Previous",
                    callback_data=prev_callback,
                ),
                InlineKeyboardButton(
                    text="▶️ Play Song",
                    callback_data=f"media:music:open:{message_id}",
                ),
                InlineKeyboardButton(
                    text=fav_text,
                    callback_data=f"media:music:fav:{index}",
                ),
                InlineKeyboardButton(
                    text="➡️ Next",
                    callback_data=next_callback,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Search",
                    callback_data="media:music:search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="media:music",
                )
            ],
        ]
    )


def music_favorites_empty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎼 Songs",
                    callback_data="media:music:songs:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="media:music",
                )
            ],
        ]
    )


def music_favorites_gallery_keyboard(
    index: int,
    total: int,
    message_id: int,
) -> InlineKeyboardMarkup:

    if total > 1:
        prev_callback = f"media:music:favs:{(index - 1) % total}"
        next_callback = f"media:music:favs:{(index + 1) % total}"
    else:
        prev_callback = "media:noop"
        next_callback = "media:noop"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Previous",
                    callback_data=prev_callback,
                ),
                InlineKeyboardButton(
                    text="▶️ Play Song",
                    callback_data=f"media:music:open:{message_id}",
                ),
                InlineKeyboardButton(
                    text="💔 Remove from Favorites",
                    callback_data=f"media:music:favremove:{index}",
                ),
                InlineKeyboardButton(
                    text="➡️ Next",
                    callback_data=next_callback,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="media:music",
                )
            ],
        ]
    )


def search_results_keyboard(
    kind: str,
    items: list[dict],
    page: int,
) -> InlineKeyboardMarkup:

    return _items_page_keyboard(
        items,
        page,
        open_prefix=f"media:{kind}:open:",
        page_prefix=f"media:{kind}:searchpage",
        back_callback=f"media:{kind}:cancel_search",
    )


# =========================================================
# SEARCH PROMPT
# =========================================================

def search_prompt_keyboard(kind: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"media:{kind}:cancel_search",
                )
            ]
        ]
    )
