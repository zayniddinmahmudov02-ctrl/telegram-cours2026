import logging

from loader import dp

from middlewares import SubscriptionMiddleware, UserTrackingMiddleware

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
    homework,
)

logging.basicConfig(level=logging.INFO)

subscription = SubscriptionMiddleware()

# Outer middleware on the Update observer runs before dispatch
# to any specific event type, so it covers every update kind
# (messages, callbacks, inline queries, chat member updates, ...)
# and always runs before the subscription check below.
dp.update.outer_middleware(UserTrackingMiddleware())

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
    homework,
]

for router in routers:
    dp.include_router(router)