import asyncio
import logging
from typing import List, Tuple

logger = logging.getLogger("ChurchBot.bot")

# Limit concurrency to avoid hitting Telegram rate limits
DEFAULT_CONCURRENCY = 20

async def _safe_send(bot, chat_id: int, text: str):
    """
    Safely send a message to a chat. Returns True if success, False if fail.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        logger.info("Message sent to chat %s", chat_id)
        return True
    except Exception as e:
        logger.warning("Send failed to %s: %s", chat_id, e)
        return False

async def broadcast_to_chats(
    bot,
    message: str,
    chat_ids: List[int],
    concurrency: int = DEFAULT_CONCURRENCY
) -> Tuple[int, int]:
    """
    Broadcast a message to multiple chats concurrently.
    Returns (success_count, fail_count).
    """
    if not chat_ids:
        logger.warning("No chat IDs provided for broadcast.")
        return 0, 0

    sem = asyncio.Semaphore(concurrency)

    async def _send_with_sem(cid):
        async with sem:
            return await _safe_send(bot, cid, message)

    tasks = [asyncio.create_task(_send_with_sem(cid)) for cid in chat_ids]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    success = sum(1 for r in results if r is True)
    failed = len(results) - success

    logger.info("Broadcast completed. Success: %s, Failed: %s", success, failed)
    return success, failed

# Centralized error handler for the app
async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)
    try:
        if update and getattr(update, "effective_message", None):
            await update.effective_message.reply_text(
                "⚠️ Something went wrong. Please try again later."
            )
    except Exception as e:
        logger.error("Failed to send error message to user: %s", e)
