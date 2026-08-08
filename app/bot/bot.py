
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers import (
    activity,
    coach,
    dashboard,
    food,
    sleep,
    start,
    statistics,
    water,
    weight,
)
from app.utils.logger import logger


def create_bot(token: str | None = None) -> Bot:
    """Instantiate aiogram 3.x Bot with HTML/Markdown parsing."""
    bot = Bot(
        token=token or settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    return bot


def create_dispatcher() -> Dispatcher:
    """Instantiate and configure aiogram 3.x Dispatcher with all feature routers."""
    dp = Dispatcher(storage=MemoryStorage())

    # Include all modular routers
    dp.include_router(start.router)
    dp.include_router(dashboard.router)
    dp.include_router(food.router)
    dp.include_router(activity.router)
    dp.include_router(weight.router)
    dp.include_router(sleep.router)
    dp.include_router(water.router)
    dp.include_router(statistics.router)
    dp.include_router(coach.router)

    from aiogram.exceptions import TelegramBadRequest
    from aiogram.types import ErrorEvent

    @dp.errors()
    async def global_error_handler(event: ErrorEvent):
        if isinstance(event.exception, TelegramBadRequest) and "message is not modified" in str(event.exception).lower():
            return True
        logger.error(f"Global handler exception on update: {event.exception}", exc_info=True)
        return True

    return dp
