# handlers/user_handlers.py
import json
import random
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from utils.translate_utils import translate_auto

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 Available commands:\n"
        "/start - Welcome message\n"
        "/cmd - Show commands list\n"
        "/verse - Daily Bible verse\n"
        "/prayer - Prayer request\n"
        "/events - Upcoming church events\n"
        "/daily_inspiration - Daily inspiration\n"
        "/myid - Show your user ID\n"
        "/chatid - Show this chat ID\n"
        "/tran - Translate text\n"
        "/quiz - Start a quiz\n"
        "/addadmin - Add admin\n"
        "/listadmins - List admins\n"
        "/deladmin - Delete admin\n"
        "/broadcast - Broadcast message\n"
        "/broadcast_users - Broadcast to users"
    )
    await update.message.reply_text(text)


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
        "👉 Type /cmd to see the full list of commands."
    )
    await update.message.reply_text(text)


async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(DATA_DIR / "verse.json", "r", encoding="utf-8") as f:
            verses = json.load(f).get("verses", [])
        if not verses:
            await update.message.reply_text("No verses available right now.")
            return
        chosen = random.choice(verses)
        await update.message.reply_text(f"📖 {chosen}")
    except Exception as e:
        logger.exception("Error loading verse.json: %s", e)
        await update.message.reply_text("Error loading verses.")


async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 Prayer request received. May God bless you.")


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(DATA_DIR / "events.json", "r", encoding="utf-8") as f:
            events = json.load(f).get("events", [])
        if not events:
            await update.message.reply_text("No events scheduled.")
            return
        text_lines = ["📅 Upcoming Events:"]
        for ev in events:
            line = f"- {ev['title']} on {ev['date']} at {ev['time']}"
            text_lines.append(line)
        await update.message.reply_text("\n".join(text_lines))
    except Exception as e:
        logger.exception("Error loading events.json: %s", e)
        await update.message.reply_text("Error loading events.")


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Today's inspiration: 'The Lord is my shepherd; I shall not want.'")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your user ID is: {update.effective_user.id}")


async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"This chat ID is: {update.effective_chat.id}")


async def tran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage:
      /tran some text
      or reply to a message with /tran
      optional: /tran en  (translate to English) or /tran my (translate to Myanmar)
    """
    try:
        args = context.args or []
        target = None
        if args and args[0].lower() in ("en", "my"):
            target = args[0].lower()
            text = " ".join(args[1:]) if len(args) > 1 else ""
        else:
            text = " ".join(args)

        if update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text

        if not text:
            await update.message.reply_text("ဘာကို translate လုပ်ချင်လဲ။ /tran <text> သို့မဟုတ် message ကို reply လုပ်ပြီး /tran ပို့ပါ။")
            return

        tgt = target if target in ("en", "my") else None
        translated = translate_auto(text, target=tgt)

        reply = f"Original:\n{text}\n\nTranslated:\n{translated}"
        await update.message.reply_text(reply)
    except Exception as e:
        logger.exception("Error in /tran: %s", e)
        await update.message.reply_text("Translation failed. တစ်ခါထပ်ကြိုးစားပါ။")
