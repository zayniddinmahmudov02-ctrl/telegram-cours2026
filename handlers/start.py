from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import db_execute
from keyboards import main_menu
from middlewares.subscription import check_subscription

router = Router()