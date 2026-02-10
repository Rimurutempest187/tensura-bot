import logging
from telegram import Update
from telegram.ext import ContextTypes
import json
from pathlib import Path

logger = logging.getLogger(__name__)
DATA_DIR = Path("data")
EVENTS_FILE = DATA_DIR / "events.json"

# --- Helper functions for events ---
def _load_events():
    if EVENTS_FILE.exists():
        return json.load(EVENTS_FILE.open("r", encoding="utf-8")).get("events", [])
    return []

def _save_events(events):
    EVENTS_FILE.write_text(
        json.dumps({"events": events}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# --- Admin Commands ---
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Add admin command executed.")

async def listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 List of admins.")

async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Delete admin command executed.")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    # Placeholder: integrate with broadcast_to_chats for groups later
    await update.message.reply_text(f"📢 Broadcast message sent: {message}")

async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast_users <message>")
        return
    message = " ".join(context.args)
    # Placeholder: integrate with broadcast_to_chats for users later
    await update.message.reply_text(f"📢 Broadcast to users executed: {message}")

async def addevent(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    _save_events([])
    await update.message.reply_text("🗑️ All events cleared.")
