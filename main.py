import asyncio
import os
from aiohttp import web

from app.bot.bot import create_bot, create_dispatcher
from app.config import settings
from app.services.firebase_service import firebase_service
from app.utils.logger import logger


async def health_check(request):
    """Health check endpoint for cloud hosting free tiers."""
    return web.Response(text="FitTrack AI Bot is 100% healthy and running 24/7 on Cloud!", status=200)


async def start_health_server():
    """Start lightweight HTTP server so cloud platforms (Render Free Web Service, Koyeb, etc.) can keep it alive 24/7."""
    port_str = os.getenv("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080

    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check web server started on port {port} (Ready for Free Web Service).")


async def main():
    logger.info("Starting FitTrack AI Telegram Bot...")
    logger.info(f"Firebase Status: {'Connected to Cloud Firestore' if firebase_service.is_connected_to_firebase else 'Local Adapter Mode'}")

    # Start health server for 100% Free Web Service cloud hosting
    await start_health_server()

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
