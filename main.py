import sqlite3
import random
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ================= CONFIG =================

BOT_TOKEN = "8372081478:AAFxalS9jm1_q7WiAZsFrEmn5F7bQxFAHs4"

ADMIN_IDS = [1812962224]   # <-- Your Telegram ID

DB_FILE = "bot.db"

START_COINS = 500
DAILY_BONUS = 100

RARITY_CHANCE = {
    "Common": 60,
    "Rare": 25,
    "Epic": 10,
    "Legendary": 5
}

RARITY_EMOJI = {
    "Common": "🌱",
    "Rare": "🔮",
    "Epic": "🔥",
    "Legendary": "👑"
}

# ================= LOG =================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= DATABASE =================

def db():
    return sqlite3.connect(DB_FILE)

def init_db():

    con = db()
    cur = con.cursor()

    # Users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER
    )
    """)

    # Characters
    cur.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY,
        name TEXT,
        rarity TEXT,
        price INTEGER,
        faction TEXT,
        file_id TEXT
    )
    """)

    # Inventory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        char_id INTEGER
    )
    """)

    con.commit()
    con.close()

# ================= USER =================

def get_user(uid):

    con = db()
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users VALUES (?,?)",
            (uid, START_COINS)
        )
        con.commit()
        coins = START_COINS
    else:
        coins = user[1]

    con.close()
    return coins

def update_coins(uid, amount):

    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET coins=? WHERE user_id=?",
        (amount, uid)
    )

    con.commit()
    con.close()

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    coins = get_user(uid)

    await update.message.reply_text(
        f"🤖 Welcome!\n\n💰 Coins: {coins}\n\n"
        "/store - Shop\n"
        "/summon - Gacha\n"
        "/inv - Inventory\n"
        "/bal - Balance"
    )

# ================= BALANCE =================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    coins = get_user(uid)

    await update.message.reply_text(
        f"💳 Balance: {coins} coins"
    )

# ================= SAVE PHOTO (ADMIN) =================

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        return

    if not update.message.photo:
        return

    caption = update.message.caption or ""
    parts = [p.strip() for p in caption.split("|")]

    name = parts[0] if len(parts) >= 1 else "Unknown"
    rarity = parts[1].capitalize() if len(parts) >= 2 else "Common"
    price = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 100
    faction = parts[3] if len(parts) >= 4 else "Unknown"

    file_id = update.message.photo[-1].file_id

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO characters
    (name,rarity,price,faction,file_id)
    VALUES (?,?,?,?,?)
    """, (name, rarity, price, faction, file_id))

    con.commit()
    con.close()

    await update.message.reply_text(
        f"✅ Saved: {name} ({rarity})"
    )

# ================= STORE =================

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    con = db()
    cur = con.cursor()

    cur.execute("SELECT * FROM characters")
    chars = cur.fetchall()

    con.close()

    if not chars:
        await update.message.reply_text("❌ No characters")
        return

    char = random.choice(chars)

    cid, name, rarity, price, faction, file_id = char

    text = (
        f"{RARITY_EMOJI[rarity]} *{name}*\n"
        f"⭐ {rarity}\n"
        f"💰 {price}\n"
        f"🏷 {faction}"
    )

    kb = [
        [InlineKeyboardButton("🛒 Buy", callback_data=f"buy_{cid}")]
    ]

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=file_id,
        caption=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= BUY =================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE, cid):

    query = update.callback_query
    uid = query.from_user.id

    coins = get_user(uid)

    con = db()
    cur = con.cursor()

    cur.execute("SELECT price FROM characters WHERE id=?", (cid,))
    row = cur.fetchone()

    if not row:
        await query.answer("Invalid")
        return

    price = row[0]

    if coins < price:
        await query.answer("Not enough coins")
        return

    update_coins(uid, coins - price)

    cur.execute(
        "INSERT INTO inventory(user_id,char_id) VALUES(?,?)",
        (uid, cid)
    )

    con.commit()
    con.close()

    await query.edit_message_caption("✅ Purchased!")

# ================= INVENTORY =================

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT c.name,c.rarity
    FROM inventory i
    JOIN characters c ON i.char_id=c.id
    WHERE i.user_id=?
    """, (uid,))

    items = cur.fetchall()
    con.close()

    if not items:
        await update.message.reply_text("📦 Empty")
        return

    text = "📦 Inventory\n\n"

    for i, c in enumerate(items, 1):
        text += f"{i}. {RARITY_EMOJI[c[1]]} {c[0]}\n"

    await update.message.reply_text(text)

# ================= GACHA =================

def roll():

    r = random.randint(1, 100)
    s = 0

    for k, v in RARITY_CHANCE.items():
        s += v
        if r <= s:
            return k

    return "Common"

async def summon(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    coins = get_user(uid)

    if coins < 100:
        await update.message.reply_text("❌ Need 100 coins")
        return

    rarity = roll()

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM characters WHERE rarity=?",
        (rarity,)
    )

    chars = cur.fetchall()

    if not chars:
        await update.message.reply_text("❌ No chars")
        return

    char = random.choice(chars)

    update_coins(uid, coins - 100)

    cur.execute(
        "INSERT INTO inventory(user_id,char_id) VALUES(?,?)",
        (uid, char[0])
    )

    con.commit()
    con.close()

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=char[5],
        caption=f"🎲 Summoned {char[1]} ({rarity})"
    )

# ================= ADMIN GIVE =================

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

    coins = get_user(target)

    update_coins(target, coins + amount)

    await update.message.reply_text("✅ Coins given")

# ================= CALLBACK =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.data.startswith("buy_"):
        cid = int(q.data.split("_")[1])
        await buy(update, context, cid)

# ================= MAIN =================

def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bal", balance))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("inv", inventory))
    app.add_handler(CommandHandler("summon", summon))
    app.add_handler(CommandHandler("give_coin", give_coin))

    app.add_handler(MessageHandler(filters.PHOTO, save_photo))
    app.add_handler(CallbackQueryHandler(buttons))

    logger.info("Bot Started")
    app.run_polling()


if __name__ == "__main__":
    main()
