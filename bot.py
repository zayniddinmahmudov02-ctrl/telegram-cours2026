import logging

from loader import dp

# Middlewares
from middlewares import SubscriptionMiddleware

# Routers
from handlers.start import router as start_router
from handlers.artikel import (
    router as artikel_router,
)
from handlers.profile import router as profile_router
from handlers.wordgame import router as wordgame_router
from handlers.quiz_callback import router as quiz_router
from handlers.ranking import router as ranking_router
from handlers.xp import router as xp_router
from handlers.video import router as video_router
logging.basicConfig(level=logging.INFO)

subscription = SubscriptionMiddleware()

dp.message.middleware(subscription)
dp.callback_query.middleware(subscription)

dp.include_router(start_router)
dp.include_router(artikel_router)
dp.include_router(profile_router)
dp.include_router(wordgame_router)
dp.include_router(quiz_router)
dp.include_router(ranking_router)
dp.include_router(xp_router)
dp.include_router(video_router)