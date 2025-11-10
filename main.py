"""Main entry point for ChatQuestBot."""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from database import Database
from bot.handlers import user, operator
from bot.utils.scheduler import start_scheduler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot."""
    try:
        # Validate configuration
        Config.validate()

        # Initialize database
        db = Database()
        logger.info("Database initialized")

        # Initialize bot and dispatcher
        bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        dp = Dispatcher()

        # Register routers
        dp.include_router(user.router)
        dp.include_router(operator.router)

        logger.info("Routers registered")

        # Start scheduler
        await start_scheduler(bot)

        # Start polling
        logger.info("Bot started successfully!")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)