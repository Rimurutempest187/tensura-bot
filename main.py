# main.py
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# telegram imports with safe fallback for Request
try:
    from telegram.request import Request
except Exception:
    try:
        from telegram.utils.request import Request
    except Exception as e:
        raise ImportError(
            "Cannot import Request from telegram. Ensure python-telegram-bot v20.x is installed "
            "and there is no conflicting 'telegram' package. Original error: " + str(e)
        )

from telegram import Update
from telegram.error import NetworkError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

import config
from utils.json_utils import init_data_files
from utils.bot_utils import error_handler as bot_error_handler
from handlers import user_handlers, quiz_handlers, admin_handlers, broadcast_handlers

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ChurchBot")

# Ensure data folders & files
DATA_DIR = getattr(config, "DATA_DIR", "data")
Path(DATA_DIR).mkdir(exist_ok=True)
init_data_files(DATA_DIR)


def build_request_from_env() -> Request:
    """
    Build a telegram Request object using sensible timeouts and optional proxy from env.
    Supported env vars:
      - TELEGRAM_PROXY (http://user:pass@host:port)
      - HTTPS_PROXY / HTTP_PROXY
    """
    proxy = os.getenv("TELEGRAM_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    request_kwargs = {
        "connect_timeout": int(os.getenv("TG_CONNECT_TIMEOUT", "10")),
        "read_timeout": int(os.getenv("TG_READ_TIMEOUT", "20")),
        "write_timeout": int(os.getenv("TG_WRITE_TIMEOUT", "20")),
        "con_pool_size": int(os.getenv("TG_CONN_POOL", "8")),
    }
    if proxy:
        request_kwargs["proxy_url"] = proxy
        logger.info("Using proxy for Telegram requests: %s", proxy)
    return Request(**request_kwargs)


def register_handlers(app):
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


def main():
    if not getattr(config, "BOT_TOKEN", None):
        raise SystemExit("BOT_TOKEN missing in config.py")

    request = build_request_from_env()
    app = ApplicationBuilder().token(config.BOT_TOKEN).request(request).build()

    register_handlers(app)

    max_retries = int(os.getenv("BOT_START_RETRIES", "5"))
    backoff_base = int(os.getenv("BOT_BACKOFF_SECONDS", "5"))
    attempt = 0

    while True:
        try:
            logger.info("Starting bot (attempt %d)", attempt + 1)
            # run_polling blocks until stopped or an exception occurs
            app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
            logger.info("Bot stopped normally.")
            break
        except NetworkError as e:
            attempt += 1
            logger.exception("NetworkError while starting/running bot: %s", e)
            if attempt >= max_retries:
                logger.error("Exceeded max start retries (%d). Exiting.", max_retries)
                sys.exit(1)
            sleep_for = backoff_base * attempt
            logger.info("Retrying in %s seconds...", sleep_for)
            time.sleep(sleep_for)
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            sys.exit(1)


if __name__ == "__main__":
    main()
