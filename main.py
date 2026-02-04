import os
import json
import random
import logging
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from dotenv import load_dotenv

import config


# ============================
# LOAD ENV
# ============================

load_dotenv()


# ============================
# LOGGING
# ============================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)

logger = logging.getLogger("ChurchBot")


# ============================
# CREATE PATHS
# ============================

def ensure_paths():

    Path(config.DATA_DIR).mkdir(exist_ok=True)

    Path(config.MEDIA_PDFS).mkdir(parents=True, exist_ok=True)
    Path(config.MEDIA_AUDIO).mkdir(parents=True, exist_ok=True)
    Path(config.MEDIA_IMAGES).mkdir(parents=True, exist_ok=True)

    def create_file(path, default):

        if not os.path.exists(path):

            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)


    create_file(config.USERS_FILE, {})
    create_file(config.QUIZZES_FILE, [])
    create_file(config.EVENTS_FILE, [])
    create_file(config.VERSES_FILE, [])


ensure_paths()


# ============================
# JSON HELPERS
# ============================

def load_json(path, default):

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:

        logger.warning("Load failed: %s", e)
        return default


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================
# USER SYSTEM
# ============================

def add_user(uid, username=None, name=None):

    users = load_json(config.USERS_FILE, {})

    uid = str(uid)

    if uid not in users:

        users[uid] = {
            "username": username,
            "full_name": name,
            "quiz_score": 0,
            "prayer_requests": [],
        }

    else:

        users[uid]["username"] = username
        users[uid]["full_name"] = name


    save_json(config.USERS_FILE, users)


def get_users():

    users = load_json(config.USERS_FILE, {})

    return [int(x) for x in users.keys()]


def is_admin(uid):

    return uid in config.ADMIN_IDS


# ============================
# COMMANDS
# ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = update.effective_user

    name = f"{u.first_name or ''} {u.last_name or ''}".strip()

    add_user(u.id, u.username, name)

    msg = (
        "🙌 Welcome!\n\n"
        "This is Church Community Bot.\n"
        "Type /cmd to see commands."
    )

    await update.message.reply_text(msg)


# ----------------------------

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
/start - Register
/cmd - All commands
/verse - Random verse
/prayer <text> - Prayer
/events - Events
/quiz - Quiz
/answer <A/B/C/D> - Answer
/tops - Ranking
/daily_inspiration - Daily Word
"""

    await update.message.reply_text(text)


# ----------------------------

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_json(config.VERSES_FILE, [])

    if not data:
        await update.message.reply_text("No verses yet.")
        return

    await update.message.reply_text("📖 " + random.choice(data))


# ----------------------------

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Use: /prayer <text>")
        return

    u = update.effective_user

    add_user(u.id, u.username, u.first_name)

    users = load_json(config.USERS_FILE, {})

    uid = str(u.id)

    text = " ".join(context.args)

    users[uid]["prayer_requests"].append({
        "text": text,
        "time": datetime.now().isoformat()
    })

    save_json(config.USERS_FILE, users)

    await update.message.reply_text("🙏 Prayer saved.")


# ----------------------------

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_json(config.EVENTS_FILE, [])

    if not data:
        await update.message.reply_text("No events.")
        return

    msg = "🗓 EVENTS\n\n"

    for e in data:
        msg += f"{e.get('name')} - {e.get('time')}\n"

    await update.message.reply_text(msg)


# ----------------------------

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_json(config.QUIZZES_FILE, [])

    if not data:
        await update.message.reply_text("No quiz.")
        return

    q = random.choice(data)

    context.user_data["answer"] = q["answer"]

    msg = f"❓ {q['question']}\n\n"

    for c in q["choices"]:
        msg += c + "\n"

    msg += "\nReply: /answer A/B/C/D"

    await update.message.reply_text(msg)


# ----------------------------

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "answer" not in context.user_data:
        await update.message.reply_text("Start quiz first.")
        return

    if not context.args:
        await update.message.reply_text("Use: /answer A")
        return

    user_ans = context.args[0].upper()

    correct = context.user_data["answer"].upper()

    u = update.effective_user

    users = load_json(config.USERS_FILE, {})

    uid = str(u.id)

    if user_ans == correct:

        users[uid]["quiz_score"] += 1

        save_json(config.USERS_FILE, users)

        await update.message.reply_text(
            f"✅ Correct! Score: {users[uid]['quiz_score']}"
        )

    else:

        await update.message.reply_text(
            f"❌ Wrong. Correct: {correct}"
        )


# ----------------------------

async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):

    users = load_json(config.USERS_FILE, {})

    if not users:
        await update.message.reply_text("No data.")
        return

    rank = []

    for u, d in users.items():

        name = d.get("username") or d.get("full_name") or "Unknown"

        rank.append((name, d.get("quiz_score", 0)))

    rank.sort(key=lambda x: x[1], reverse=True)

    msg = "🏆 TOP PLAYERS\n\n"

    for i, (n, s) in enumerate(rank[:10], 1):
        msg += f"{i}. {n} — {s}\n"

    await update.message.reply_text(msg)


# ----------------------------

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = [
        "Trust in the Lord. 🙏",
        "God is with you. ✨",
        "Keep praying. 💙",
        "Faith over fear. 🌟",
        "Jesus loves you. ❤️",
    ]

    await update.message.reply_text(random.choice(data))


# ============================
# ERROR
# ============================

async def error(update, context):

    logger.error("Error", exc_info=context.error)


# ============================
# MAIN
# ============================

def main():

    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing")


    app = ApplicationBuilder()\
        .token(config.BOT_TOKEN)\
        .build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmd", cmd))

    app.add_handler(CommandHandler("verse", verse))
    app.add_handler(CommandHandler("prayer", prayer))
    app.add_handler(CommandHandler("events", events))

    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("answer", answer))
    app.add_handler(CommandHandler("tops", tops))

    app.add_handler(CommandHandler("daily_inspiration", daily))

    app.add_error_handler(error)


    logger.info("✅ BOT STARTED")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
