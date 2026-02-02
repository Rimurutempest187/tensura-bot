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


# ----------------------
# Load ENV
# ----------------------
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
# Ensure folders/files
# ----------------------
def ensure_paths():

    Path("data").mkdir(exist_ok=True)
    Path(config.MEDIA_PDFS).mkdir(parents=True, exist_ok=True)
    Path(config.MEDIA_AUDIO).mkdir(parents=True, exist_ok=True)
    Path(config.MEDIA_IMAGES).mkdir(parents=True, exist_ok=True)

    def ensure_file(path, default):

        p = Path(path)

        if not p.exists():
            p.write_text(
                json.dumps(default, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

    ensure_file(config.USERS_FILE, {})
    ensure_file(config.QUIZZES_FILE, [])
    ensure_file(config.EVENTS_FILE, [])
    ensure_file(config.VERSES_FILE, [])


ensure_paths()


# ----------------------
# JSON Helpers
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
# User Management
# ----------------------
def add_user_if_missing(user_id, username=None, full_name=None):

    users = load_json(config.USERS_FILE, {})

    uid = str(user_id)

    if uid not in users:

        users[uid] = {
            "prayer_requests": [],
            "language": "en",
            "quiz_score": 0,
            "username": username,
            "full_name": full_name
        }

    else:

        # Update name if changed
        users[uid]["username"] = username
        users[uid]["full_name"] = full_name

    save_json(config.USERS_FILE, users)


def get_all_user_ids():

    users = load_json(config.USERS_FILE, {})

    return [int(uid) for uid in users.keys()]


def is_admin(user_id):

    return user_id in (config.ADMIN_IDS or [])


# ----------------------
# Commands
# ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user_if_missing(
        user.id,
        user.username,
        f"{user.first_name or ''} {user.last_name or ''}".strip()
    )

    await update.message.reply_text(
        "🙏 Welcome to Church Youth Bot!\n"
        "Use /help to see commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "/start - Register\n"
        "/help - Help\n"
        "/verse - Random verse\n"
        "/prayer <text> - Prayer request\n"
        "/events - Events\n"
        "/quiz - Start quiz\n"
        "/answer <text> - Answer quiz\n"
        "/tops - Ranking\n"
        "/daily_inspiration - Motivation\n"
        "/broadcast <text> - Admin\n"
        "/send_pdf <file> - Admin\n"
        "/send_audio <file> - Admin\n"
        "/send_image <file> - Admin"
    )

    await update.message.reply_text(text)


# ----------------------
# Verse
# ----------------------
async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    verses = load_json(config.VERSES_FILE, [])

    if not verses:
        await update.message.reply_text("No verses available.")
        return

    await update.message.reply_text(
        f"📖 {random.choice(verses)}"
    )


# ----------------------
# Prayer
# ----------------------
async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user_if_missing(
        user.id,
        user.username,
        f"{user.first_name or ''} {user.last_name or ''}".strip()
    )

    if not context.args:
        await update.message.reply_text(
            "Usage: /prayer <your request>"
        )
        return

    users = load_json(config.USERS_FILE, {})

    uid = str(user.id)

    text = " ".join(context.args)

    users[uid]["prayer_requests"].append({
        "text": text,
        "time": datetime.now().isoformat()
    })

    save_json(config.USERS_FILE, users)

    await update.message.reply_text("🙏 Saved.")


# ----------------------
# Events
# ----------------------
async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    events = load_json(config.EVENTS_FILE, [])

    if not events:
        await update.message.reply_text("No events.")
        return

    msg = ["🗓 Events:\n"]

    for e in events:
        msg.append(
            f"{e.get('name')} — {e.get('time')}"
        )

    await update.message.reply_text("\n".join(msg))


# ----------------------
# Quiz
# ----------------------
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user_if_missing(
        user.id,
        user.username,
        f"{user.first_name or ''} {user.last_name or ''}".strip()
    )

    q = get_random_quiz()

    if not q:
        await update.message.reply_text("No quiz.")
        return

    context.user_data["quiz_answer"] = q.get("Answer")

    await update.message.reply_text(
        f"❓ {q.get('Question')}"
    )


# ----------------------
# Answer
# ----------------------
async def answer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user_if_missing(
        user.id,
        user.username,
        f"{user.first_name or ''} {user.last_name or ''}".strip()
    )

    if "quiz_answer" not in context.user_data:
        await update.message.reply_text(
            "Use /quiz first."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /answer <text>"
        )
        return

    user_answer = " ".join(context.args)

    correct = context.user_data["quiz_answer"]

    if check_answer(user_answer, correct):

        users = load_json(config.USERS_FILE, {})

        uid = str(user.id)

        users[uid]["quiz_score"] += 1

        save_json(config.USERS_FILE, users)

        await update.message.reply_text(
            "✅ Correct! +1 Point"
        )

    else:

        await update.message.reply_text(
            f"❌ Wrong! Answer: {correct}"
        )


# ----------------------
# Ranking
# ----------------------
async def tops_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    users = load_json(config.USERS_FILE, {})

    if not users:
        await update.message.reply_text("No data.")
        return

    ranking = []

    for uid, data in users.items():

        score = data.get("quiz_score", 0)

        name = (
            f"@{data['username']}"
            if data.get("username")
            else data.get("full_name", "Unknown")
        )

        ranking.append((name, score))

    ranking.sort(
        key=lambda x: x[1],
        reverse=True
    )

    text = "🏆 TOP QUIZ PLAYERS\n\n"

    for i, (name, score) in enumerate(ranking[:10], 1):
        text += f"{i}. {name} — {score} pts\n"

    await update.message.reply_text(text)


# ----------------------
# Inspiration
# ----------------------
async def daily_inspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msgs = [
        "🌟 Stay faithful!",
        "🙏 God is with you.",
        "✨ Keep going!",
        "🕊️ Peace today."
    ]

    await update.message.reply_text(
        random.choice(msgs)
    )


# ----------------------
# Media (Admin)
# ----------------------
async def send_pdf(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ No access")
        return

    if not context.args:
        await update.message.reply_text("Usage: /send_pdf <file>")
        return

    path = os.path.join(
        config.MEDIA_PDFS,
        context.args[0]
    )

    if not os.path.exists(path):
        await update.message.reply_text("Not found.")
        return

    with open(path, "rb") as f:
        await update.message.reply_document(f)


async def send_audio(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ No access")
        return

    if not context.args:
        await update.message.reply_text("Usage: /send_audio <file>")
        return

    path = os.path.join(
        config.MEDIA_AUDIO,
        context.args[0]
    )

    if not os.path.exists(path):
        await update.message.reply_text("Not found.")
        return

    with open(path, "rb") as f:
        await update.message.reply_audio(f)


async def send_image(update, context):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ No access")
        return

    if not context.args:
        await update.message.reply_text("Usage: /send_image <file>")
        return

    path = os.path.join(
        config.MEDIA_IMAGES,
        context.args[0]
    )

    if not os.path.exists(path):
        await update.message.reply_text("Not found.")
        return

    with open(path, "rb") as f:
        await update.message.reply_photo(f)


# ----------------------
# Error Handler
# ----------------------
async def error_handler(update, context):

    logger.exception(context.error)

    for aid in (config.ADMIN_IDS or []):

        try:
            await context.bot.send_message(
                chat_id=aid,
                text=f"Error: {context.error}"
            )
        except:
            pass


# ----------------------
# Main
# ----------------------
def main():

    app = ApplicationBuilder() \
        .token(config.BOT_TOKEN) \
        .build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("prayer", prayer))
    app.add_handler(CommandHandler("events", events_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("answer", answer_command))
    app.add_handler(CommandHandler("tops", tops_command))
    app.add_handler(CommandHandler("daily_inspiration", daily_inspiration))

    app.add_handler(CommandHandler("send_pdf", send_pdf))
    app.add_handler(CommandHandler("send_audio", send_audio))
    app.add_handler(CommandHandler("send_image", send_image))

    # Broadcast
    try:
        import importlib

        b = importlib.import_module("broadcast")

        if hasattr(b, "broadcast_command"):
            app.add_handler(
                CommandHandler("broadcast", b.broadcast_command)
            )

    except Exception as e:
        logger.warning("Broadcast not loaded: %s", e)

    app.add_error_handler(error_handler)

    # Scheduler
    try:
        start_scheduler(app.bot, get_all_user_ids)
    except Exception as e:
        logger.error("Scheduler error: %s", e)

    logger.info("Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()
