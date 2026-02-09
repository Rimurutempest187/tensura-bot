import json, random, logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from utils.translate_utils import translate_auto
from db import SessionLocal
from models import Prayer

logger = logging.getLogger(__name__)
DATA_DIR = Path("data")
VERSE_FILE = DATA_DIR / "verse.json"
EVENTS_FILE = DATA_DIR / "events.json"
PRAYER_FILE = DATA_DIR / "prayers.json"

def _load_json(path, default):
    try:
        if not path.exists():
            path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
            return default
        return json.load(path.open("r", encoding="utf-8"))
    except Exception as e:
        logger.exception("Error loading %s: %s", path, e)
        return default

def _save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# --- User Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "✝️ Welcome to Church Community Bot ✝️\n\n"
        "Here you will find:\n"
        "✨ Daily inspiration\n"
        "📖 Bible verses\n"
        "🤲 Prayers\n"
        "📅 Church events\n"
        "🎯 Quizzes and uplifting activities\n\n"
        "This bot is here to help us grow closer to God and to one another in fellowship.\n\n"
        "👉 Type /cmd to see the full list of commands.\n\n"
        )
    await update.message.reply_text(text)

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 User Commands:\n"
        "/start - Welcome\n"
        "/cmd - Show commands\n"
        "/verse - Daily Bible verse\n"
        "/prayer - Add prayer request\n"
        "/prayerlist - Show prayer requests\n"
        "/events - Upcoming events\n"
        "/daily_inspiration - Daily inspiration\n"
        "/myid - Show your ID\n"
        "/chatid - Show chat ID\n"
        "/tran - Translate text\n"
        "/quiz - Start quiz"
    )

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = _load_json(VERSE_FILE, {"verses": ["Psalm 23:1"]})
    verses = data.get("verses", [])
    await update.message.reply_text("📖 " + random.choice(verses))

# handlers/user_handlers.py


async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("သင့်ဆုတောင်းကို /prayer <text> အနေနဲ့ ရေးပေးပါ။")
        return
    session = SessionLocal()
    prayer = Prayer(user=update.effective_user.username or update.effective_user.full_name, text=text)
    session.add(prayer)
    session.commit()
    session.close()
    await update.message.reply_text("🙏 သင့်ဆုတောင်းကို Database ထဲသိမ်းပြီးပါပြီ။")

async def prayerlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    prayers = session.query(Prayer).all()
    session.close()
    if not prayers:
        await update.message.reply_text("🙏 ဆုတောင်းစာရင်း မရှိသေးပါ။")
        return
    lines = ["🙏 Prayer Requests:"]
    for p in prayers:
        lines.append(f"- {p.user}: {p.text}")
    await update.message.reply_text("\n".join(lines))


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    evs = _load_json(EVENTS_FILE, {"events": []}).get("events", [])
    if not evs:
        await update.message.reply_text("No events scheduled.")
        return
    lines = ["📅 Upcoming Events:"]
    for ev in evs:
        lines.append(f"- {ev['title']} on {ev['date']} {ev['time']}")
    await update.message.reply_text("\n".join(lines))

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Today's inspiration: 'The Lord is my shepherd.'")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your user ID is: {update.effective_user.id}")

async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"This chat ID is: {update.effective_chat.id}")

async def tran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args or []
        target = args[0].lower() if args and args[0].lower() in ("en", "my") else None
        text = " ".join(args[1:]) if target else " ".join(args)
        if update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text
        if not text:
            await update.message.reply_text("Usage: /tran <text> or reply to a message with /tran")
            return
        translated = translate_auto(text, target=target)
        await update.message.reply_text(f"Original:\n{text}\n\nTranslated:\n{translated}")
    except Exception as e:
        logger.exception("Error in /tran: %s", e)
        await update.message.reply_text("Translation failed.")
