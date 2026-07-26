from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def test(message: Message):
    print("INFO ROUTER:", message.text)
    await message.answer("TEST")