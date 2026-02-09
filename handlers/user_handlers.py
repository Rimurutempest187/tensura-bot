# handlers/user_handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.translate_utils import translate_auto

logger = logging.getLogger(__name__)
# handlers/user_handlers.py (example)
async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Available commands: /start /tran /quiz ...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome. Use /tran <text> or reply to a message with /tran")

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
