from telegram.ext import ContextTypes
from config import ADMIN_IDS
import logging
import json

logger = logging.getLogger(__name__)

async def broadcast_command(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)

    # Load all user IDs
    try:
        with open("data/users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
        user_ids = [int(uid) for uid in users.keys()]
    except Exception as e:
        await update.message.reply_text("Failed to load users.json")
        logger.warning("Failed to load users.json: %s", e)
        return

    count = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            count += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")
