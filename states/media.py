from aiogram.fsm.state import State, StatesGroup


class MediaSearchState(StatesGroup):
    waiting_book_query = State()
    waiting_movie_query = State()
    waiting_music_query = State()
