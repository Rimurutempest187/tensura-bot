from telegram import Update
from telegram.ext import ContextTypes
import config
from utils.json_utils import load_json
from utils.bot_utils import broadcast_to_chats

GROUPS_FILE = getattr(config, "GROUPS_FILE", "data/groups.json")
USERS_FILE = getattr(config, "USERS_FILE", "data/users.json")

# Define admin IDs here directly
ADMIN_IDS = [123456789, 987654321]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)

    # load configured groups from config and persisted groups
    groups = getattr(config, "GROUP_IDS", []) or []
    persisted = await load_json(GROUPS_FILE, [])
    chat_ids = list(dict.fromkeys(list(groups) + list(persisted)))

    ok, fail = await broadcast_to_chats(context.bot, message, chat_ids)
    await update.message.reply_text(f"✅ Broadcast to groups: Sent {ok}, Failed {fail}")

async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast_users <message>")
        return
    message = " ".join(context.args)

    users = await load_json(USERS_FILE, {})
    user_ids = [int(k) for k in users.keys()]

    ok, fail = await broadcast_to_chats(context.bot, message, user_ids)
    await update.message.reply_text(f"✅ Broadcast to users: Sent {ok}, Failed {fail}")
