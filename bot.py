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
    media,
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
    media,
]

for router in routers:
    dp.include_router(router)