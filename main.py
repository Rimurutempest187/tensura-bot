import json
import logging
import os
import random
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [
    123456789  # <- သင့် Telegram ID ထည့်ပါ
]

DB_FILE = "bot.db"
CHAR_FILE = "characters.json"

# ================= LOG =================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ================= DATABASE =================


def db():
    return sqlite3.connect(DB_FILE)


def init_db():
    con = db()
    cur = con.cursor()

    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 100
    )
    """)

    # cards
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        char_id INTEGER
    )
    """)

    # favorites
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fav (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        rarity TEXT,
        image_url TEXT
    )
    """)

    con.commit()
    con.close()


# ================= CHAR =================


def load_chars():
    with open(CHAR_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


RARITY_EMOJI = {
    "Common": "🌱",
    "Rare": "🔮",
    "Epic": "🔥",
    "Legendary": "👑"
}


# ================= USER =================


def get_user(user_id: int):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users(user_id,coins) VALUES(?,100)",
            (user_id,)
        )
        con.commit()

    con.close()


def get_coins(user_id):
    con = db()
    cur = con.cursor()

    cur.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    c = cur.fetchone()[0]

    con.close()
    return c


def add_coins(user_id, amount):
    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET coins = coins + ? WHERE user_id=?",
        (amount, user_id)
    )

    con.commit()
    con.close()


# ================= COMMANDS =================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    get_user(user_id)

    coins = get_coins(user_id)

    text = f"""
🌌 Welcome {update.effective_user.first_name}

💰 Coins: {coins}

Commands:
/store
/bal
/admin
"""

    await update.message.reply_text(text)


# ================= STORE =================


async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chars = load_chars()
    char = random.choice(chars)

    emoji = RARITY_EMOJI.get(char["rarity"], "❓")

    text = f"""
{emoji} {char['name']}
⭐ {char['rarity']}
💰 {char['price']} Coins
"""

    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 Buy",
                callback_data=f"buy_{char['id']}"
            )
        ]
    ]

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=char["image_url"],
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= BUY =================


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    char_id = int(query.data.split("_")[1])

    chars = load_chars()

    char = next(c for c in chars if c["id"] == char_id)

    coins = get_coins(user_id)

    if coins < char["price"]:
        await query.edit_message_caption("❌ Not enough coins")
        return

    # deduct
    add_coins(user_id, -char["price"])

    # save card
    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO cards(user_id,char_id) VALUES(?,?)",
        (user_id, char_id)
    )

    con.commit()
    con.close()

    await query.edit_message_caption(
        f"✅ Purchased {char['name']}!"
    )


# ================= BALANCE =================


async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    coins = get_coins(user_id)

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM cards WHERE user_id=?",
        (user_id,)
    )

    cards = cur.fetchone()[0]

    con.close()

    text = f"""
💳 Balance

💰 Coins: {coins}
🏆 Cards: {cards}
"""

    await update.message.reply_text(text)


# ================= ADMIN =================


def is_admin(user_id):
    return user_id in ADMIN_IDS


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    text = """
👑 ADMIN PANEL

/give_coin user_id amount
/give_char user_id char_id
"""

    await update.message.reply_text(text)


async def give_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
    except:
        await update.message.reply_text("Usage: /give_coin id amount")
        return

    get_user(uid)
    add_coins(uid, amount)

    await update.message.reply_text("✅ Coins Given")


async def give_char(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    try:
        uid = int(context.args[0])
        cid = int(context.args[1])
    except:
        await update.message.reply_text("Usage: /give_char id char_id")
        return

    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO cards(user_id,char_id) VALUES(?,?)",
        (uid, cid)
    )

    con.commit()
    con.close()

    await update.message.reply_text("✅ Character Given")


# ================= MAIN =================


def main():

    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("give_coin", give_coin))
    app.add_handler(CommandHandler("give_char", give_char))

    # buttons
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))

    print("🤖 Bot Started")
    app.run_polling()


if __name__ == "__main__":
    main()
