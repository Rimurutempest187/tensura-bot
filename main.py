import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import config

from handlers.quiz import quiz, button
from handlers.admin import addadmin, listadmins, deladmin
from handlers.broadcast import broadcast_cmd, broadcast_users_cmd
from handlers.user import start, cmd, verse, prayer, events, tops, daily, myid, chatid
from utils.logging_utils import setup_logging

logger = setup_logging()

async def error_handler(update, context):
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ Something went wrong. Please try again later.")

def main():
    if not getattr(config, "BOT_TOKEN", None):
        raise SystemExit("BOT_TOKEN missing in config.py")

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # user commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmd", cmd))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("prayer", prayer))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(CommandHandler("tops", tops))
    app.add_handler(CommandHandler("daily_inspiration", daily))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("chatid", chatid))

    # quiz
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(button))

    # admin
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("listadmins", listadmins))
    app.add_handler(CommandHandler("deladmin", deladmin))

    # broadcast
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("broadcast_users", broadcast_users_cmd))

    app.add_error_handler(error_handler)

    logger.info("✅ BOT STARTED")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
