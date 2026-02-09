# handlers/admin_handlers.py
import logging, json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)
DATA_DIR = Path("data")
EVENTS_FILE = DATA_DIR / "events.json"

# Admin IDs ကို သင့် Telegram User ID နဲ့ ပြောင်းပေးပါ
ADMIN_IDS = [5085103993, 987621]

def is_admin(user_id):
    return user_id in ADMIN_IDS

def _load_events():
    if EVENTS_FILE.exists():
        return json.load(EVENTS_FILE.open("r", encoding="utf-8")).get("events", [])
    return []

def _save_events(events):
    EVENTS_FILE.write_text(json.dumps({"events": events}, ensure_ascii=False, indent=2), encoding="utf-8")

# --- Admin Commands ---
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 သင့်မှာ အခွင့်မရှိပါ။")
        return
    await update.message.reply_text("👑 Admin ထည့်သွင်းပြီးပါပြီ။")

async def listadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 သင့်မှာ အခွင့်မရှိပါ။")
        return
    await update.message.reply_text("👑 Admin စာရင်းကို ပြထားပါသည်။")

async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 သင့်မှာ အခွင့်မရှိပါ။")
        return
    await update.message.reply_text("👑 Admin ဖယ်ရှားပြီးပါပြီ။")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 သင့်မှာ အခွင့်မရှိပါ။")
        return
    await update.message.reply_text("📢 Broadcast message ပို့ပြီးပါပြီ။")

async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 သင့်မှာ အခွင့်မရှိပါ။")
        return
    await update.message.reply_text("📢 Users တွေထဲကို Broadcast ပို့ပြီးပါပြီ။")

async def addevent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 သင့်မှာ အခွင့်မရှိပါ။")
        return
    text = " ".join(context.args)
    if "|" not in text:
        await update.message.reply_text("အသုံးပြုပုံ: /addevent <title> | <date> | <time>")
        return
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        await update.message.reply_text("Title, Date, Time ကို | နဲ့ ခွဲရေးပါ။")
        return
    title, date, time = parts[0], parts[1], parts[2]
    evs = _load_events()
    evs.append({"title": title, "date": date, "time": time})
    _save_events(evs)
    await update.message.reply_text(f"✅ Event ထည့်သွင်းပြီးပါပြီ: {title} on {date} at {time}")

async def clearevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 သင့်မှာ အခွင့်မရှိပါ။")
        return
    _save_events([])
    await update.message.reply_text("🗑️ Event စာရင်းအားလုံး ဖျက်ပြီးပါပြီ။")
