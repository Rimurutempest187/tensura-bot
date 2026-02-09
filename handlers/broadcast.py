import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from utils.json_utils import load_json
import config
from handlers.admin import is_admin

USERS_FILE = f"{config.DATA_DIR}/users.json"
GROUPS_FILE = f"{config.DATA_DIR}/groups.json"

def get_users_list():
    users = load_json(USERS_FILE, {})
    return [int(k) for k in users.keys()]

def load_saved_groups():
    return load_json(GROUPS_FILE, [])

async def broadcast_to(bot, ids, message: str):
    tasks = [bot.send_message(chat_id=i, text=message) for i in ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    success = sum(1 for r in results if not isinstance(r, Exception))
    fail = sum(1 for r in results if isinstance(r, Exception))
    return success, fail

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    groups = getattr(config, "GROUP_IDS", []) + load_saved_groups()
    ok, fail = await broadcast_to(context.bot, groups, message)
    await update.message.reply_text(f"✅ Broadcast to groups: Sent {ok}, Failed {fail}")

async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast_users <message>")
        return
    message = " ".join(context.args)
    ok, fail = await broadcast_to(context.bot, get_users_list(), message)
    await update.message.reply_text(f"✅ Broadcast to users: Sent {ok}, Failed {fail}")
