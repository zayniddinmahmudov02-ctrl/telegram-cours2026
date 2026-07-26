from .start import router as start
from .artikel import router as artikel
from .profile import router as profile
from .wordgame import router as wordgame
from .quiz_callback import router as quiz
from .xp import router as xp
from .video import router as video
from .admin import router as admin
from .payment import router as payment
from .broadcast import router as broadcast
from .private_message import router as private_message
from .info import router as info
from .leaderboard import router as leaderboard

__all__ = [
    "start",
    "artikel",
    "profile",
    "wordgame",
    "quiz",
    "xp",
    "video",
    "admin",
    "payment",
    "broadcast",
    "private_message",
    "info",
    "leaderboard",
]