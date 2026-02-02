import asyncio
import random
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

logger = logging.getLogger(__name__)

def start_scheduler(bot, get_user_ids):
    """
    Start a scheduler to send daily inspiration to all users.
    `get_user_ids` is a function returning a list of Telegram IDs.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")

    async def daily_message():
        samples = [
            "🌟 Keep your faith strong!",
            "🙏 God is always with you.",
            "✨ Small acts of love change the world.",
            "🕊️ Peace be with you today."
        ]
        user_ids = get_user_ids()
        for uid in user_ids:
            try:
                await bot.send_message(chat_id=uid, text=random.choice(samples))
            except Exception as e:
                logger.warning("Failed to send daily inspiration to %s: %s", uid, e)

    # Schedule the job daily at 08:00 UTC
    scheduler.add_job(lambda: asyncio.create_task(daily_message()), 'cron', hour=8, minute=0)
    scheduler.start()
    logger.info("Scheduler started for daily inspiration")
