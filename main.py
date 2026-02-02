# main.py
import os
import json
import random
import logging
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

import config
from reminder import start_scheduler
from games import get_random_quiz, check_answer

# Load .env (config.py also loads it; keeping load here is harmless)
load_dotenv()

# ----------------------
# Logging
# ----------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------
# Ensure data folders/files
# ----------------------
def ensure_paths():
    Path("data").mkdir(exist_ok=True)
    Path(config.MEDIA_PDFS).mkdir(parents=True, exist_ok=True)
    Path(config.MEDIA_AUDIO).mkdir(parents=True, exist_ok=True)
    Path(config.MEDIA_IMAGES).mkdir(parents=True, exist_ok=True)

    def ensure_file(path, default):
        p = Path(path)
        if not p.exists():
            p.write_text(json.dumps(default, ensure_ascii=False, indent=2))
    ensure_file(config.USERS_FILE, {})
    ensure_file(config.QUIZZES_FILE, [])
    ensure_file(config.EVENTS_FILE, [])
    ensure_file(config.VERSES_FILE, [])

ensure_paths()

# ----------------------
# Utilities
# ----------------------
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------
# User management
# ----------------------
def add_user_if_missing(user_id: int):
    users = load_json(config.USERS_FILE, {})
    key = str(user_id)
    if key not in users:
        users[key] = {"prayer_requests": [], "language": "en"}
        save_json(config.USERS_FILE, users)
        logger.info("Added new user %s", user_id)

def get_all_user_ids():
    users = load_json(config.USERS_FILE, {})
    return [int(uid) for uid in users.keys()]

def is_admin(user_id: int) -> bool:
    return user_id in (config.ADMIN_IDS or [])

# ----------------------
# Command handlers
# ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user_if_missing(user.id)
    await update.message.reply_text(
        "🙏 Welcome to Church Youth Bot!\nUse /help to see commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - Register\n"
        "/help - This help\n"
        "/verse - Get a random verse\n"
        "/prayer <text> - Submit a prayer request\n"
        "/events - Show events\n"
        "/quiz - Start a quiz\n"
        "/answer <text> - Answer the quiz\n"
        "/daily_inspiration - Motivational message\n"
        "/broadcast <text> - Admin broadcast\n"
        "/send_pdf <filename> - Admin send PDF\n"
        "/send_audio <filename> - Admin send audio\n"
        "/send_image <filename> - Admin send image"
    )
    await update.message.reply_text(text)

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verses = load_json(config.VERSES_FILE, [])
    if not verses:
        await update.message.reply_text("No verses available.")
        return
    await update.message.reply_text(f"📖 {random.choice(verses)}")

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /prayer <your prayer request>")
        return
    user_id = str(update.effective_user.id)
    add_user_if_missing(update.effective_user.id)
    users = load_json(config.USERS_FILE, {})
    text = " ".join(context.args)
    users.setdefault(user_id, {}).setdefault("prayer_requests", []).append({
        "text": text,
        "time": datetime.now().isoformat()
    })
    save_json(config.USERS_FILE, users)
    await update.message.reply_text("🙏 Prayer request recorded.")

async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = load_json(config.EVENTS_FILE, [])
    if not events:
        await update.message.reply_text("No events.")
        return
    lines = ["🗓 Upcoming events:"]
    for e in events:
        lines.append(f"{e.get('name', 'Unnamed')} — {e.get('time', 'Unknown')}")
    await update.message.reply_text("\n".join(lines))

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = get_random_quiz()
    if not q:
        await update.message.reply_text("No quizzes found.")
        return
    context.user_data["quiz_answer"] = q.get("Answer", "")
    await update.message.reply_text(f"❓ Quiz: {q.get('Question', '')}")

async def answer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "quiz_answer" not in context.user_data:
        await update.message.reply_text("Start a quiz first with /quiz")
        return
    if not context.args:
        await update.message.reply_text("Usage: /answer <your answer>")
        return
    user_answer = " ".join(context.args)
    correct = context.user_data.get("quiz_answer")
    if check_answer(user_answer, correct):
        await update.message.reply_text("✅ Correct!")
    else:
        await update.message.reply_text(f"❌ Wrong. Correct: {correct}")

async def daily_inspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    samples = [
        "🌟 Keep your faith strong!",
        "🙏 God is always with you.",
        "✨ Small acts of love change the world.",
        "🕊️ Peace be with you today."
    ]
    await update.message.reply_text(random.choice(samples))

# ----------------------
# Multimedia commands (explicit, clear)
# ----------------------
async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_pdf <filename>")
        return
    filename = context.args[0]
    path = os.path.join(config.MEDIA_PDFS, filename)
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    with open(path, "rb") as f:
        await update.message.reply_document(document=f)

async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_audio <filename>")
        return
    filename = context.args[0]
    path = os.path.join(config.MEDIA_AUDIO, filename)
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    with open(path, "rb") as f:
        await update.message.reply_audio(audio=f)

async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Not authorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_image <filename>")
        return
    filename = context.args[0]
    path = os.path.join(config.MEDIA_IMAGES, filename)
    if not os.path.exists(path):
        await update.message.reply_text("❌ File not found.")
        return
    with open(path, "rb") as f:
        await update.message.reply_photo(photo=f)

# ----------------------
# Error handler
# ----------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Update caused error: %s", context.error)
    # notify admins
    for aid in (config.ADMIN_IDS or []):
        try:
            await context.bot.send_message(chat_id=aid, text=f"Bot error: {context.error}")
        except Exception:
            pass

# ----------------------
# Main (entrypoint)
# ----------------------
def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("prayer", prayer))
    app.add_handler(CommandHandler("events", events_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("answer", answer_command))
    app.add_handler(CommandHandler("daily_inspiration", daily_inspiration))
    app.add_handler(CommandHandler("send_pdf", send_pdf))
    app.add_handler(CommandHandler("send_audio", send_audio))
    app.add_handler(CommandHandler("send_image", send_image))

    # Broadcast handler: import lazily to reduce chance of circular import during module load
    try:
        import importlib
        broadcast_mod = importlib.import_module("broadcast")
        if hasattr(broadcast_mod, "broadcast_command"):
            app.add_handler(CommandHandler("broadcast", broadcast_mod.broadcast_command))
    except Exception as e:
        logger.warning("Broadcast module not loaded: %s", e)

    app.add_error_handler(error_handler)

    # Start the scheduler and pass the function to fetch user IDs (avoid circular import)
    try:
        start_scheduler(app.bot, get_all_user_ids)
    except Exception as e:
        logger.exception("Failed to start scheduler: %s", e)

    # Start polling (this will run until interrupted)
    logger.info("Church Youth Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
