import logging

from loader import dp

from middlewares import SubscriptionMiddleware

from handlers import (
    start,
    artikel,
    profile,
    wordgame,
    quiz,
    xp,
    video,
    admin,
    payment,
    broadcast,
    private_message,
    info,
    leaderboard,

    # Homework
    homework,
    homework_online,
    homework_video,
    homework_speaking,
    teacher_homework,
    teacher_chat,
)

logging.basicConfig(level=logging.INFO)

subscription = SubscriptionMiddleware()

dp.message.middleware(subscription)
dp.callback_query.middleware(subscription)

routers = [
    start,
    artikel,
    profile,
    wordgame,
    quiz,
    xp,
    video,
    admin,
    payment,
    broadcast,
    private_message,
    info,
    leaderboard,

    # Homework
    homework,
    homework_online,
    homework_video,
    homework_speaking,
    teacher_homework,
    teacher_chat,
]

for router in routers:
    dp.include_router(router)