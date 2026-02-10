import json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import config

GROUPS_FILE = Path(config.GROUPS_FILE)

def _load_groups():
    if GROUPS_FILE.exists():
        data = json.load(GROUPS_FILE.open("r", encoding="utf-8"))
        return data.get("groups", [])
    return []

def _save_groups(groups):
    GROUPS_FILE.write_text(json.dumps({"groups": groups}, ensure_ascii=False, indent=2), encoding="utf-8")

def is_admin(user_id: int) -> bool:
    from handlers.admin_handlers import _load_admins
    return user_id in _load_admins()

# --- Commands ---
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
