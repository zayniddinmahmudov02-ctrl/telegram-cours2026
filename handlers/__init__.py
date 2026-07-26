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

# Homework
from .homework import router as homework
from .homework_online import router as homework_online
from .homework_video import router as homework_video
from .homework_speaking import router as homework_speaking
from .teacher_homework import router as teacher_homework
from .teacher_chat import router as teacher_chat


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

    # Homework
    "homework",
    "homework_online",
    "homework_video",
    "homework_speaking",
    "teacher_homework",
    "teacher_chat",
]