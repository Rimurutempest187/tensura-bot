# main.py
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Try to import Request from python-telegram-bot; if unavailable, continue without custom Request
Request = None
try:
    from telegram.request import Request  # python-telegram-bot v20+
except Exception:
    try:
        from telegram.utils.request import Request  # fallback (rare)
    except Exception:
        Request = None

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
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
init_data_files(DATA_DIR)


def build_request_from_env():
    if Request is None:
        logger.debug("telegram.request.Request not available; using default request settings.")
        return None

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


def safe_add_command(app, command_name: str, handler_module, handler_attr: str):
    """Add a CommandHandler only if the handler exists in the module."""
    if hasattr(handler_module, handler_attr):
        handler_func = getattr(handler_module, handler_attr)
        app.add_handler(CommandHandler(command_name, handler_func))
        logger.debug("Registered /%s -> %s.%s", command_name, handler_module.__name__, handler_attr)
    else:
        logger.warning("Handler missing: %s.%s not found. Skipping /%s registration.",
                       handler_module.__name__, handler_attr, command_name)


def safe_add_callback(app, handler_module, handler_attr: str, callback_class):
    """Add a callback handler (e.g., CallbackQueryHandler) if exists."""
    if hasattr(handler_module, handler_attr):
        handler_func = getattr(handler_module, handler_attr)
        app.add_handler(callback_class(handler_func))
        logger.debug("Registered callback handler %s.%s", handler_module.__name__, handler_attr)
    else:
        logger.warning("Callback handler missing: %s.%s not found. Skipping.", handler_module.__name__, handler_attr)


def register_handlers(app):
    # --- User Commands ---
    safe_add_command(app, "start", user_handlers, "start")
    safe_add_command(app, "cmd", user_handlers, "cmd")
    safe_add_command(app, "verse", user_handlers, "verse")
    safe_add_command(app, "prayer", user_handlers, "prayer")
    safe_add_command(app, "prayerlist", user_handlers, "prayerlist")
    safe_add_command(app, "events", user_handlers, "events")
    safe_add_command(app, "daily_inspiration", user_handlers, "daily")
    safe_add_command(app, "myid", user_handlers, "myid")
    safe_add_command(app, "chatid", user_handlers, "chatid")
    safe_add_command(app, "tran", user_handlers, "tran")
    safe_add_command(app, "quiz", quiz_handlers, "quiz")
    safe_add_callback(app, quiz_handlers, "quiz_button", CallbackQueryHandler)

    # --- Admin Commands ---
    safe_add_command(app, "addadmin", admin_handlers, "addadmin")
    safe_add_command(app, "listadmins", admin_handlers, "listadmins")
    safe_add_command(app, "deladmin", admin_handlers, "deladmin")
    safe_add_command(app, "broadcast", admin_handlers, "broadcast_cmd")
    safe_add_command(app, "broadcast_users", admin_handlers, "broadcast_users_cmd")
    safe_add_command(app, "addevent", admin_handlers, "addevent")
    safe_add_command(app, "clearevents", admin_handlers, "clearevents")

    # --- Error Handler ---
    app.add_error_handler(bot_error_handler)


def main():
    if not getattr(config, "BOT_TOKEN", None):
        raise SystemExit("BOT_TOKEN missing in config.py")

    request = build_request_from_env()
    if request is not None:
        app = ApplicationBuilder().token(config.BOT_TOKEN).request(request).build()
    else:
        app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    # main.py
from scheduler import start_scheduler
    # register handlers
    register_handlers(app)
    # start scheduler
    scheduler = start_scheduler()
    # run bot
    app.run_polling()
    register_handlers(app)

    max_retries = int(os.getenv("BOT_START_RETRIES", "6"))
    backoff_base = int(os.getenv("BOT_BACKOFF_SECONDS", "5"))
    attempt = 0

    while True:
        try:
            logger.info("Starting bot (attempt %d)", attempt + 1)
            app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
            logger.info("Bot stopped normally.")
            break
        except NetworkError as e:
            attempt += 1
            logger.exception("NetworkError while running bot: %s", e)
            if attempt >= max_retries:
                logger.error("Exceeded max retries (%d). Exiting.", max_retries)
                sys.exit(1)
            sleep_for = backoff_base * attempt
            logger.info("Retrying in %s seconds...", sleep_for)
            time.sleep(sleep_for)
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received. Shutting down.")
            try:
                app.stop()
            except Exception:
                pass
            sys.exit(0)
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            sys.exit(1)


if __name__ == "__main__":
    main()
