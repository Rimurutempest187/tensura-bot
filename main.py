# main.py
import logging
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import config
from utils.json_utils import init_data_files
from utils.bot_utils import error_handler as bot_error_handler
from handlers import user_handlers, quiz_handlers, admin_handlers, broadcast_handlers

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ChurchBot")

# Ensure data folders & files
DATA_DIR = getattr(config, "DATA_DIR", "data")
Path(DATA_DIR).mkdir(exist_ok=True)
init_data_files(DATA_DIR)

def main():
    if not getattr(config, "BOT_TOKEN", None):
        raise SystemExit("BOT_TOKEN missing in config.py")

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Basic user commands
    app.add_handler(CommandHandler("start", user_handlers.start))
    app.add_handler(CommandHandler("cmd", user_handlers.cmd))
    app.add_handler(CommandHandler("verse", user_handlers.verse))
    app.add_handler(CommandHandler("prayer", user_handlers.prayer))
    app.add_handler(CommandHandler("events", user_handlers.events))
    app.add_handler(CommandHandler("tops", user_handlers.tops))
    app.add_handler(CommandHandler("daily_inspiration", user_handlers.daily))
    app.add_handler(CommandHandler("myid", user_handlers.myid))
    app.add_handler(CommandHandler("chatid", user_handlers.chatid))
    app.add_handler(CommandHandler("tran", user_handlers.tran))

    # Quiz (uses inline buttons)
    app.add_handler(CommandHandler("quiz", quiz_handlers.quiz))
    app.add_handler(CallbackQueryHandler(quiz_handlers.quiz_button))

    # Admin
    app.add_handler(CommandHandler("addadmin", admin_handlers.addadmin))
    app.add_handler(CommandHandler("listadmins", admin_handlers.listadmins))
    app.add_handler(CommandHandler("deladmin", admin_handlers.deladmin))

    # Broadcast
    app.add_handler(CommandHandler("broadcast", broadcast_handlers.broadcast_cmd))
    app.add_handler(CommandHandler("broadcast_users", broadcast_handlers.broadcast_users_cmd))

    # Centralized error handler
    app.add_error_handler(bot_error_handler)

    logger.info("✅ BOT STARTED")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
