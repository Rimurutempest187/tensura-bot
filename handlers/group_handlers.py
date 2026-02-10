import json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)
DATA_DIR = Path("data")
GROUPS_FILE = DATA_DIR / "groups.json"

def _load_groups():
    if GROUPS_FILE.exists():
        try:
            data = json.load(GROUPS_FILE.open("r", encoding="utf-8"))
            if isinstance(data, dict) and "groups" in data:
                groups = data.get("groups", [])
            elif isinstance(data, list):
                groups = data
            else:
                groups = []
            out = []
            for g in groups:
                try:
                    out.append(int(g))
                except Exception:
                    logger.warning("Invalid group id in groups.json: %s", g)
            return list(dict.fromkeys(out))
        except Exception as e:
            logger.exception("Failed to read groups.json: %s", e)
            return []
    return []

def _save_groups(groups):
    try:
        GROUPS_FILE.write_text(json.dumps({"groups": groups}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.exception("Failed to write groups.json: %s", e)

def is_admin(user_id: int) -> bool:
    try:
        from handlers.admin_handlers import _load_admins
        return user_id in _load_admins()
    except Exception:
        return False

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /addgroup <group_id>")
        return
    try:
        gid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid group ID.")
        return
    groups = _load_groups()
    if gid not in groups:
        groups.append(gid)
        _save_groups(groups)
        await update.message.reply_text(f"✅ Group added: {gid}")
    else:
        await update.message.reply_text("⚠️ Already in group list.")

async def listgroups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    groups = _load_groups()
    if not groups:
        await update.message.reply_text("⚠️ No groups saved.")
    else:
        await update.message.reply_text(f"👥 Groups: {groups}")

async def delgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /delgroup <group_id>")
        return
    try:
        gid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid group ID.")
        return
    groups = _load_groups()
    if gid in groups:
        groups.remove(gid)
        _save_groups(groups)
        await update.message.reply_text(f"🗑️ Group removed: {gid}")
    else:
        await update.message.reply_text("⚠️ Group not found.")

# Optional: auto-save when bot is added to a group (my_chat_member updates)
async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        if not chat:
            return
        if chat.type not in ("group", "supergroup"):
            return
        groups = _load_groups()
        if chat.id not in groups:
            groups.append(chat.id)
            _save_groups(groups)
            logger.info("Auto-saved group id %s to groups.json", chat.id)
    except Exception as e:
        logger.exception("on_my_chat_member error: %s", e)
