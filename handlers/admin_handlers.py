import logging
import json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from utils.bot_utils import broadcast_to_chats

logger = logging.getLogger(__name__)
DATA_DIR = Path("data")
ADMINS_FILE = DATA_DIR / "admins.json"
EVENTS_FILE = DATA_DIR / "events.json"
GROUPS_FILE = DATA_DIR / "groups.json"
USERS_FILE = DATA_DIR / "users.json"

# --- Helper functions ---
def _load_admins():
    if ADMINS_FILE.exists():
        return json.load(ADMINS_FILE.open("r", encoding="utf-8")).get("admins", [])
    return []

def _save_admins(admins):
    ADMINS_FILE.write_text(json.dumps({"admins": admins}, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_events():
    if EVENTS_FILE.exists():
        return json.load(EVENTS_FILE.open("r", encoding="utf-8")).get("events", [])
    return []

def _save_events(events):
    EVENTS_FILE.write_text(json.dumps({"events": events}, ensure_ascii=False, indent=2), encoding="utf-8")

def _load_groups():
    if GROUPS_FILE.exists():
        data = json.load(GROUPS_FILE.open("r", encoding="utf-8"))
        return data.get("groups", [])
    return []

def _load_users():
    if USERS_FILE.exists():
        data = json.load(USERS_FILE.open("r", encoding="utf-8"))
        return [int(uid) for uid in data.keys()]
    return []

def is_admin(user_id: int) -> bool:
    return user_id in _load_admins()

# --- Admin Commands ---
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /addadmin <user_id>")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user ID.")
        return
    admins = _load_admins()
    if user_id not in admins:
        admins.append(user_id)
        _save_admins(admins)
        await update.message.reply_text(f"👑 Admin added: {user_id}")
    else:
        await update.message.reply_text("⚠️ Already an admin.")

async def listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    admins = _load_admins()
    if not admins:
        await update.message.reply_text("⚠️ No admins saved.")
    else:
        await update.message.reply_text(f"👑 Current admins: {admins}")

async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /deladmin <user_id>")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user ID.")
        return
    admins = _load_admins()
    if user_id in admins:
        admins.remove(user_id)
        _save_admins(admins)
        await update.message.reply_text(f"👑 Admin removed: {user_id}")
    else:
        await update.message.reply_text("⚠️ Not found in admin list.")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    groups = _load_groups()
    if not groups:
        await update.message.reply_text("⚠️ No groups configured.")
        return
    await update.message.reply_text(f"📤 Broadcasting to {len(groups)} groups...")
    ok, fail = await broadcast_to_chats(context.bot, message, groups)
    await update.message.reply_text(f"✅ Broadcast completed. Sent: {ok}, Failed: {fail}")

async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast_users <message>")
        return
    message = " ".join(context.args)
    users = _load_users()
    if not users:
        await update.message.reply_text("⚠️ No users found.")
        return
    await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")
    ok, fail = await broadcast_to_chats(context.bot, message, users)
    await update.message.reply_text(f"✅ Broadcast completed. Sent: {ok}, Failed: {fail}")

async def addevent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    text = " ".join(context.args)
    if "|" not in text:
        await update.message.reply_text("Usage: /addevent <title> | <date> | <time>")
        return
    title, date, time = [p.strip() for p in text.split("|")]
    evs = _load_events()
    evs.append({"title": title, "date": date, "time": time})
    _save_events(evs)
    await update.message.reply_text(f"✅ Event added: {title} on {date} at {time}")

async def clearevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized.")
        return
    _save_events([])
    await update.message.reply_text("🗑️ All events cleared.")
