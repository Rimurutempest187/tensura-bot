# handlers/admin_handlers.py
from typing import Set
from telegram import Update
from telegram.ext import ContextTypes

import config
from utils.json_utils import load_json, save_json

ADMIN_FILE = getattr(config, "ADMIN_FILE", "data/admins.json")
ADMINS: Set[int] = set(int(x) for x in getattr(config, "ADMIN_IDS", []))

async def load_admins():
    extra = await load_json(ADMIN_FILE, [])
    try:
        extra_ints = [int(x) for x in extra]
    except Exception:
        extra_ints = []
    ADMINS.update(extra_ints)

# call once at import time
import asyncio
asyncio.get_event_loop().run_until_complete(load_admins())

def is_admin(uid: int) -> bool:
    return int(uid) in ADMINS

async def persist_admins():
    base = set(int(x) for x in getattr(config, "ADMIN_IDS", []))
    extras = list(sorted(ADMINS - base))
    await save_json(ADMIN_FILE, extras)

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    target = None
    if context.args:
        try:
            target = int(context.args[0])
        except Exception:
            await update.message.reply_text("❌ Invalid ID format.")
            return
    elif update.message.reply_to_message:
        target = update.message.reply_to_message.from_user.id
    else:
        await update.message.reply_text("Usage: /addadmin <user_id>  OR reply to a user's message with /addadmin")
        return

    if target in ADMINS:
        await update.message.reply_text("⚠️ Already admin.")
        return

    ADMINS.add(int(target))
    await persist_admins()
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
    try:
        target = int(context.args[0])
    except Exception:
        await update.message.reply_text("❌ Invalid ID.")
        return

    base = set(int(x) for x in getattr(config, "ADMIN_IDS", []))
    if target in base:
        await update.message.reply_text("❌ Cannot remove owner defined in config.py.")
        return

    if target not in ADMINS:
        await update.message.reply_text("⚠️ Not an admin.")
        return

    ADMINS.remove(target)
    await persist_admins()
    await update.message.reply_text(f"✅ Removed admin: {target}")
