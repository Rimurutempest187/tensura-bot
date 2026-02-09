# handlers/quiz_handlers.py
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import config
from utils.json_utils import load_json, save_json

QUIZZES_FILE = getattr(config, "QUIZZES_FILE", "data/quizzes.json")
USERS_FILE = getattr(config, "USERS_FILE", "data/users.json")

# Send a quiz with inline buttons
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await load_json(QUIZZES_FILE, [])
    if not data:
        await update.message.reply_text("No quiz.")
        return
    q = random.choice(data)
    # store correct answer in user_data
    context.user_data["answer"] = q["answer"].upper()
    context.user_data["question_id"] = q.get("id")

    # build keyboard from choices (assume choices like "A. text")
    choices = q.get("choices", [])
    buttons = []
    row = []
    for i, c in enumerate(choices):
        label = c.split(".", 1)[0].strip() if "." in c else chr(65 + i)
        row.append(InlineKeyboardButton(label, callback_data=label))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    reply_markup = InlineKeyboardMarkup(buttons)
    text = f"❓ {q['question']}\n\n" + "\n".join(choices)
    await update.message.reply_text(text, reply_markup=reply_markup)

# Handle button presses
async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_ans = query.data.upper()
    correct = context.user_data.get("answer", "").upper()
    if not correct:
        await query.edit_message_text("Start quiz first with /quiz")
        return

    u = update.effective_user
    users = await load_json(USERS_FILE, {})
    uid = str(u.id)
    if uid not in users:
        users[uid] = {"username": u.username, "full_name": u.first_name, "quiz_score": 0, "prayer_requests": [], "first_seen": None}

    if user_ans == correct:
        users[uid]["quiz_score"] = users[uid].get("quiz_score", 0) + 1
        await save_json(USERS_FILE, users)
        await query.edit_message_text(f"✅ Correct! Score: {users[uid]['quiz_score']}")
    else:
        await query.edit_message_text(f"❌ Wrong. Correct: {correct}")
