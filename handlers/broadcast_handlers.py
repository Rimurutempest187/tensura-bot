import logging
from telegram import Update
from telegram.ext import ContextTypes
import config
from utils.json_utils import load_json, save_json
from utils.bot_utils import broadcast_to_chats

logger = logging.getLogger(__name__)

GROUPS_FILE = getattr(config, "GROUPS_FILE", "data/groups.json")
USERS_FILE = getattr(config, "USERS_FILE", "data/users.json")


async def _load_persisted_groups():
    """Return a list of persisted group chat IDs (may be empty)."""
    data = await load_json(GROUPS_FILE, [])
    if isinstance(data, dict) and "groups" in data:
        return data.get("groups", [])
    if isinstance(data, list):
        return data
    return []


async def _load_users_list():
    """Return a list of user IDs from users.json (may be empty)."""
    data = await load_json(USERS_FILE, {})
    if isinstance(data, dict):
        try:
            return [int(k) for k in data.keys()]
        except Exception:
            return []
    return []


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast a message to configured groups (config + persisted)."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)

    # Gather group chat IDs from config and persisted storage
    configured = getattr(config, "GROUP_IDS", []) or []
    persisted = await _load_persisted_groups()
    # Normalize and dedupe
    try:
        all_ids = [int(x) for x in list(dict.fromkeys(list(configured) + list(persisted)))]
    except Exception:
        all_ids = []
    if not all_ids:
        await update.message.reply_text("⚠️ No target groups configured.")
        return

    await update.message.reply_text("📤 Sending broadcast to groups...")

    try:
        ok, fail = await broadcast_to_chats(context.bot, message, all_ids)
    except Exception as e:
        logger.exception("Error while broadcasting to groups: %s", e)
        await update.message.reply_text(f"❌ Broadcast failed due to error: {e}")
        return

    summary = f"✅ Broadcast to groups completed. Sent: {ok}, Failed: {fail}"
    await update.message.reply_text(summary)


async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast a message to all known users (users.json)."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast_users <message>")
        return

    message = " ".join(context.args)

    user_ids = await _load_users_list()
    if not user_ids:
        await update.message.reply_text("⚠️ No users found to broadcast to.")
        return

    await update.message.reply_text("📤 Sending broadcast to users...")

    try:
        ok, fail = await broadcast_to_chats(context.bot, message, user_ids)
    except Exception as e:
        logger.exception("Error while broadcasting to users: %s", e)
        await update.message.reply_text(f"❌ Broadcast failed due to error: {e}")
        return

    summary = f"✅ Broadcast to users completed. Sent: {ok}, Failed: {fail}"
    await update.message.reply_text(summary)
