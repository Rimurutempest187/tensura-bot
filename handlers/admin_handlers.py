import logging, json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)
DATA_DIR = Path("data")
EVENTS_FILE = DATA_DIR / "events.json"

def _load_events():
    if EVENTS_FILE.exists():
        return json.load(EVENTS_FILE.open("r", encoding="utf-8")).get("events", [])
    return []

def _save_events(events):
    EVENTS_FILE.write_text(json.dumps({"events": events}, ensure_ascii=False, indent=2), encoding="utf-8")

# --- Admin Commands ---
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Add admin command executed.")

async def listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 List of admins.")

async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Delete admin command executed.")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Broadcast message sent.")

async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Broadcast to users executed.")

async def addevent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if "|" not in text:
        await update.message.reply_text("Usage: /addevent <title> | <date> | <time>")
        return
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        await update.message.reply_text("Please provide title, date, and time separated by |")
        return
    title, date, time = parts[0], parts[1], parts[2]
    evs = _load_events()
    evs.append({"title": title, "date": date, "time": time})
    _save_events(evs)
    await update.message.reply_text(f"✅ Event added: {title} on {date} at {time}")

async def clearevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _save_events([])
    await update.message.reply_text("🗑️ All events cleared.")
