# handlers/user_handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.translate_utils import translate_auto

logger = logging.getLogger(__name__)
# handlers/user_handlers.py (example)
async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Available commands: 
    /start — Initialize conversation; shows welcome message.
    /cmd — Show a short list of available commands or help text.
    /verse — Send a Bible verse (or configured verse content).
    /prayer — Send a prayer or prayer-related content.
    /events — List upcoming events.
    /tops — Show top items (e.g., top verses, top posts).
    /daily_inspiration — Send the daily inspiration message.
    /myid — Reply with your user ID.
    /chatid — Reply with the current chat ID.
    /tran — Translate text (see usage below).
    /quiz — Start a quiz (uses inline buttons).
    /addadmin — Add an admin (admin-only).
    /listadmins — List current admins (admin-only).
    /deladmin — Remove an admin (admin-only).
    /broadcast — Send a broadcast message (admin-only).
    /broadcast_users — Broadcast to users list (admin-only).")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✝️ Welcome to Church Community Bot ✝️

    Here you will find:
    ✨ Daily inspiration
    📖 Bible verses
    🤲 Prayers
    📅 Church events
    🎯 Quizzes and uplifting activities

    This bot is here to help us grow closer to God and to one another in fellowship.

    👉 Type /cmd to see the full list of commands.

    ")
# handlers/user_handlers.py
from telegram import Update
from telegram.ext import ContextTypes

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 Prayer request received. May God bless you.")

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Upcoming church events will be listed here.")

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
        # get target language if provided as first arg
        args = context.args or []
        target = None
        if args and args[0].lower() in ("en", "my"):
            target = args[0].lower()
            # remove the language token from text
            text = " ".join(args[1:]) if len(args) > 1 else ""
        else:
            text = " ".join(args)

        # if user replied to a message, prefer that text
        if update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text

        if not text:
            await update.message.reply_text("ဘာကို translate လုပ်ချင်လဲ။ /tran <text> သို့မဟုတ် message ကို reply လုပ်ပြီး /tran ပို့ပါ။")
            return

        # map short code to deep-translator target
        if target == "en":
            tgt = "en"
        elif target == "my":
            tgt = "my"
        else:
            tgt = None

        translated = translate_auto(text, target=tgt)
        # reply with original and translation
        reply = f"**Original:**\n{text}\n\n**Translated:**\n{translated}"
        # send as plain text (no markdown) to avoid formatting issues
        await update.message.reply_text(reply)
    except Exception as e:
        logger.exception("Error in /tran: %s", e)
        await update.message.reply_text("Translation failed. တစ်ခါထပ်ကြိုးစားပါ။")
