import asyncio
import logging

from data.settings import LOGS_PATH
from bot_loader import bot, dp
from modules.database import init_db
from modules.logs import setup_logging
import modules.handlers # noqa: F401

async def main():
    setup_logging(LOGS_PATH)
    
    logger = logging.getLogger(__name__)
    logger.info("Bot starting...")
    await init_db()
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Bot polling failed: {e}", exc_info=True)
    finally:
        logger.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())
