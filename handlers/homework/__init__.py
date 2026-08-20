from aiogram import Router

from . import access, admin, evaluation, history, menu, profile, submission

router = Router()

for sub_router in (
    access.router,
    profile.router,
    menu.router,
    submission.router,
    history.router,
    evaluation.router,
    admin.router,
):
    router.include_router(sub_router)

__all__ = ["router"]
