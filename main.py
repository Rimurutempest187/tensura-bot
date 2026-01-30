import logging
import json
import random
import os
import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)


# ================== CONFIG ==================

TOKEN = "8372081478:AAFxalS9jm1_q7WiAZsFrEmn5F7bQxFAHs4"

ADMIN_IDS = [
    1812962224  # <-- Your Telegram ID
]

DB_NAME = "bot.db"

# ============================================


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


RARITY_EMOJI = {
    "Common": "⚪",
    "Rare": "🔵",
    "Epic": "🟣",
    "Legendary": "🟡"
}


# ================== DATABASE ==================

def init_db():

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 1000
    )
    """)

    # Inventory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        char_id INTEGER,
        name TEXT,
        rarity TEXT
    )
    """)

    conn.commit()
    conn.close()


# ================== DATA ==================

def load_chars():

    with open("characters.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_user(uid):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (uid,)
    )

    user = cur.fetchone()

    if not user:

        cur.execute(
            "INSERT INTO users (user_id, coins) VALUES (?,1000)",
            (uid,)
        )

        conn.commit()

        user = (uid, 1000)

    conn.close()

    return user


def add_coins(uid, amount):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET coins = coins + ? WHERE user_id=?",
        (amount, uid)
    )

    conn.commit()
    conn.close()


def remove_coins(uid, amount):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET coins = coins - ? WHERE user_id=?",
        (amount, uid)
    )

    conn.commit()
    conn.close()


def add_inventory(uid, char):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory
    (user_id, char_id, name, rarity)
    VALUES (?,?,?,?)
    """, (
        uid,
        char["id"],
        char["name"],
        char["rarity"]
    ))

    conn.commit()
    conn.close()


def get_inventory(uid):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT name,rarity FROM inventory WHERE user_id=?",
        (uid,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows


# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    await update.message.reply_text(
        f"""
👋 Welcome {update.effective_user.first_name}

💰 Coins: {user[1]}

Commands:
/store - Shop
/bal - Balance
/inv - Inventory
"""
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    await update.message.reply_text(
        f"💰 Your Coins: {user[1]}"
    )


async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    items = get_inventory(update.effective_user.id)

    if not items:
        await update.message.reply_text("📦 Inventory empty.")
        return

    text = "📦 Your Cards:\n\n"

    for i in items:
        text += f"{RARITY_EMOJI.get(i[1],'❓')} {i[0]} ({i[1]})\n"

    await update.message.reply_text(text)


async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chars = load_chars()

    char = random.choice(chars)

    path = char["image_url"]

    text = f"""
{RARITY_EMOJI.get(char['rarity'],'❓')} {char['name']}
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

    markup = InlineKeyboardMarkup(keyboard)

    if not os.path.exists(path):

        await update.message.reply_text(
            "❌ Image missing",
            reply_markup=markup
        )
        return

    with open(path, "rb") as img:

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img,
            caption=text,
            reply_markup=markup
        )


# ================== BUY ==================

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    char_id = int(query.data.split("_")[1])

    chars = load_chars()

    char = next(
        (c for c in chars if c["id"] == char_id),
        None
    )

    if not char:
        await query.edit_message_caption("❌ Item not found")
        return

    user = get_user(uid)

    if user[1] < char["price"]:
        await query.edit_message_caption("❌ Not enough coins")
        return

    remove_coins(uid, char["price"])
    add_inventory(uid, char)

    await query.edit_message_caption(
        f"✅ Purchased {char['name']}!"
    )


# ================== ADMIN ==================

async def give_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "/give_coin user_id amount"
        )
        return

    target = int(context.args[0])
    amount = int(context.args[1])

    add_coins(target, amount)

    await update.message.reply_text("✅ Coins given")


async def give_char(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "/give_char user_id char_id"
        )
        return

    target = int(context.args[0])
    char_id = int(context.args[1])

    chars = load_chars()

    char = next(
        (c for c in chars if c["id"] == char_id),
        None
    )

    if not char:
        await update.message.reply_text("❌ Char not found")
        return

    add_inventory(target, char)

    await update.message.reply_text("✅ Character given")


# ================== MAIN ==================

def main():

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("bal", balance))
    app.add_handler(CommandHandler("inv", inventory))

    app.add_handler(CommandHandler("give_coin", give_coin))
    app.add_handler(CommandHandler("give_char", give_char))

    app.add_handler(CallbackQueryHandler(buy_callback))

    print("🤖 Bot Started...")

    app.run_polling()


if __name__ == "__main__":
    main()
