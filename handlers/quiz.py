import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.json_utils import load_json, save_json
import config

QUIZZES_FILE = f"{config.DATA_DIR}/quizzes.json"
USERS_FILE = f"{config.DATA_DIR}/users.json"

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_json(QUIZZES_FILE, [])
    if not data:
        await update.message.reply_text("No quiz.")
        return
    q = random.choice(data)
    context.user_data["answer"] = q["answer"]

    keyboard = [
        [InlineKeyboardButton("A", callback_data="A"),
         InlineKeyboardButton("B", callback_data="B")],
        [InlineKeyboardButton("C", callback_data="C"),
         InlineKeyboardButton("D", callback_data="D")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"❓ {q['question']}\n\n" + "\n".join(q["choices"]),
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_ans = query.data
    correct = context.user_data.get("answer", "").upper()
    uid = str(update.effective_user.id)
    users = load_json(USERS_FILE, {})

    if user_ans == correct:
        users[uid]["quiz_score"] = users.get(uid, {}).get("quiz_score", 0) + 1
        save_json(USERS_FILE, users)
        await query.edit_message_text(f"✅ Correct! Score: {users[uid]['quiz_score']}")
    else:
        await query.edit_message_text(f"❌ Wrong. Correct: {correct}")
