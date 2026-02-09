from telegram import Update
from telegram.ext import ContextTypes
from utils.json_utils import load_json, save_json
import config

ADMIN_FILE = f"{config.DATA_DIR}/admins.json"
ADMINS = set(load_json(ADMIN_FILE, [])) | set(getattr(config, "ADMIN_IDS", []))

def persist_admins():
    base = set(getattr(config, "ADMIN_IDS", []))
    extras = list(sorted(ADMINS - base))
    save_json(ADMIN_FILE, extras)

def is_admin(uid: int) -> bool:
    return int(uid) in ADMINS

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /addadmin <user_id>")
        return
    target = int(context.args[0])
    ADMINS.add(target)
    persist_admins()
    await update.message.reply_text(f"✅ Added admin: {target}")

async def listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    txt = "Admins:\n" + "\n".join(str(x) for x in sorted(ADMINS))
    await update.message.reply_text(txt)

async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /deladmin <user_id>")
        return
    target = int(context.args[0])
    if target in getattr(config, "ADMIN_IDS", []):
        await update.message.reply_text("❌ Cannot remove owner defined in config.py.")
        return
    ADMINS.discard(target)
    persist_admins()
    await update.message.reply_text(f"✅ Removed admin: {target}")
