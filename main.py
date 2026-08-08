import asyncio

from app.bot.bot import create_bot, create_dispatcher
from app.config import settings
from app.services.firebase_service import firebase_service
from app.utils.logger import logger


async def main():
    logger.info("Starting FitTrack AI Telegram Bot...")
    logger.info(f"Firebase Status: {'Connected to Cloud Firestore' if firebase_service.is_connected_to_firebase else 'Local Adapter Mode (Offline/Test Ready)'}")

    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "MOCK_BOT_TOKEN":
        logger.warning(
            "⚠️ TELEGRAM_BOT_TOKEN is not configured in .env. "
            "Please configure your real Telegram Bot Token from @BotFather in .env to connect to live Telegram servers."
        )

    bot = create_bot()
    dp = create_dispatcher()

    try:
        logger.info("FitTrack AI Bot is actively listening for updates...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Polling terminated: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot session closed successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("FitTrack AI Bot stopped gracefully.")
