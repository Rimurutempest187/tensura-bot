import logging
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatMemberHandler,   # အသစ်ထည့်ရန်
    filters,
)
from utils.bot_utils import error_handler as bot_error_handler
from handlers import (
    user_handlers,
    quiz_handlers,
    admin_handlers,
    group_handlers,
)

logger = logging.getLogger("ChurchBot")

def safe_add_command(app, command_name: str, handler_module, handler_attr: str):
    if hasattr(handler_module, handler_attr):
        handler_func = getattr(handler_module, handler_attr)
        app.add_handler(CommandHandler(command_name, handler_func))
        logger.debug("Registered /%s -> %s.%s", command_name, handler_module.__name__, handler_attr)

def safe_add_callback(app, handler_module, handler_attr: str):
    if hasattr(handler_module, handler_attr):
        handler_func = getattr(handler_module, handler_attr)
        app.add_handler(CallbackQueryHandler(handler_func))
        logger.debug("Registered CallbackQueryHandler -> %s.%s", handler_module.__name__, handler_attr)

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

    # Quiz
    safe_add_command(app, "quiz", quiz_handlers, "quiz")
    safe_add_callback(app, quiz_handlers, "quiz_button")

    # --- Admin Commands ---
    safe_add_command(app, "addadmin", admin_handlers, "addadmin")
    safe_add_command(app, "listadmins", admin_handlers, "listadmins")
    safe_add_command(app, "deladmin", admin_handlers, "deladmin")
    safe_add_command(app, "broadcast", admin_handlers, "broadcast_cmd")
    safe_add_command(app, "broadcast_users", admin_handlers, "broadcast_users_cmd")
    safe_add_command(app, "addevent", admin_handlers, "addevent")
    safe_add_command(app, "clearevents", admin_handlers, "clearevents")

    # --- Group management ---
    safe_add_command(app, "addgroup", group_handlers, "addgroup")
    safe_add_command(app, "listgroups", group_handlers, "listgroups")
    safe_add_command(app, "delgroup", group_handlers, "delgroup")

    # --- Optional: track users ---
    if hasattr(user_handlers, "track_user"):
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.track_user))
        logger.debug("Registered track_user message handler.")

    # --- my_chat_member updates ---
    if hasattr(group_handlers, "on_my_chat_member"):
        app.add_handler(ChatMemberHandler(group_handlers.on_my_chat_member, chat_member_types=["my_chat_member"]))
        logger.debug("Registered on_my_chat_member handler.")

    # --- Error Handler ---
    app.add_error_handler(bot_error_handler)
