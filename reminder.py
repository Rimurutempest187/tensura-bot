import asyncio
import random
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

logger = logging.getLogger(__name__)

def start_scheduler(bot, get_user_ids):
    """
    Start a scheduler to send daily inspiration to all users.
    
    Args:
        bot: Telegram Bot instance (from app.bot)
        get_user_ids: Callable that returns a list of Telegram user IDs
    """
    # Create an AsyncIO scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")

    async def daily_message():
        """
        Send a daily inspirational message to all registered users.
        """
        samples = [
            "🌟 Keep your faith strong!",
            "🙏 God is always with you.",
            "✨ Small acts of love change the world.",
            "🕊️ Peace be with you today.",
            "💖 Let your light shine before others.",
            "📖 God's word is a lamp to your feet.",
            "🌈 Trust in the Lord with all your heart.",
            "🕊️ Be still and know that He is God.",
            "🌟 Every day is a gift from God.",
            "🙏 Pray without ceasing and have faith."
        ]

        user_ids = get_user_ids()
        logger.info("Sending daily inspiration to %d users", len(user_ids))
        for uid in user_ids:
            try:
                await bot.send_message(chat_id=uid, text=random.choice(samples))
            except Exception as e:
                logger.warning("Failed to send daily inspiration to %s: %s", uid, e)

    # Schedule the job daily at 08:00 UTC
    scheduler.add_job(
        lambda: asyncio.create_task(daily_message()),
        trigger='cron',
        hour=8,
        minute=0
    )

    scheduler.start()
    logger.info("Scheduler started for daily inspiration")
