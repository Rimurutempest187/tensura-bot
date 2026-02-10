import logging
import json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from utils.bot_utils import broadcast_to_chats

logger = logging.getLogger(__name__)
DATA_DIR = Path("data")
GROUPS_FILE = DATA_DIR / "groups.json"

def _load_groups():
    if not GROUPS_FILE.exists():
        return []
    try:
        data = json.load(GROUPS_FILE.open("r", encoding="utf-8"))
        if isinstance(data, dict) and "groups" in data:
            groups = data.get("groups", [])
        elif isinstance(data, list):
            groups = data
        else:
            groups = []
        # normalize to ints and dedupe
        out = []
        for g in groups:
            try:
                out.append(int(g))
            except Exception:
                logger.warning("Invalid group id in groups.json: %s", g)
        return list(dict.fromkeys(out))
    except Exception as e:
        logger.exception("Failed to load groups.json: %s", e)
        return []

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        from handlers.admin_handlers import is_admin
    except Exception:
        logger.debug("admin_handlers.is_admin not available")
        is_admin = lambda uid: False

    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)

    # load groups from file and config.GROUP_IDS if present
    groups = _load_groups()
    try:
        import config
        cfg_ids = getattr(config, "GROUP_IDS", []) or []
        cfg_ids = [int(x) for x in cfg_ids if str(x).strip() != ""]
    except Exception:
        cfg_ids = []

    all_ids = list(dict.fromkeys(cfg_ids + groups))
    if not all_ids:
        await update.message.reply_text("⚠️ No target groups configured.")
        return

    await update.message.reply_text(f"📤 Broadcasting to {len(all_ids)} groups...")

    try:
        ok, fail = await broadcast_to_chats(context.bot, message, all_ids)
    except Exception as e:
        logger.exception("broadcast_to_chats failed: %s", e)
        # fallback: try per-chat sends
        ok = fail = 0
        for cid in all_ids:
            try:
                await context.bot.send_message(chat_id=cid, text=message)
                ok += 1
            except Exception as e2:
                logger.exception("Direct send failed to %s: %s", cid, e2)
                fail += 1

    await update.message.reply_text(f"✅ Broadcast completed. Sent: {ok}, Failed: {fail}")

async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        from handlers.admin_handlers import is_admin
    except Exception:
        logger.debug("admin_handlers.is_admin not available")
        is_admin = lambda uid: False

    if not is_admin(user.id):
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast_users <message>")
        return

    message = " ".join(context.args)

    users_file = DATA_DIR / "users.json"
    users = []
    if users_file.exists():
        try:
            data = json.load(users_file.open("r", encoding="utf-8")) or {}
            users = [int(k) for k in data.keys()]
        except Exception as e:
            logger.exception("Failed to load users.json: %s", e)
            users = []

    if not users:
        await update.message.reply_text("⚠️ No users found to broadcast to.")
        return

    await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")

    try:
        ok, fail = await broadcast_to_chats(context.bot, message, users)
    except Exception as e:
        logger.exception("broadcast_to_chats failed for users: %s", e)
        ok = fail = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=message)
                ok += 1
            except Exception as e2:
                logger.exception("Direct send failed to user %s: %s", uid, e2)
                fail += 1

    await update.message.reply_text(f"✅ Broadcast to users completed. Sent: {ok}, Failed: {fail}")
