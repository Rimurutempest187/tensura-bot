import sqlite3
import random
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto
)

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ================= CONFIG =================

BOT_TOKEN = "8372081478:AAHK5cw9n-TL6QJ4vRXYMSauJC2yX-uart8"

OWNER_ID = 1812962224   # Your Telegram ID

START_COINS = 500
SUMMON_COST = 100

DB_FILE = "bot.db"

STORE_CACHE = {}

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        coins INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(
        user_id INTEGER PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS characters(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        rarity TEXT,
        price INTEGER,
        faction TEXT,
        file_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        char_id INTEGER
    )
    """)

    con.commit()
    con.close()


# ================= UTIL =================

def is_admin(uid):

    if uid == OWNER_ID:
        return True

    con = db()
    cur = con.cursor()

    cur.execute("SELECT user_id FROM admins WHERE user_id=?", (uid,))
    r = cur.fetchone()

    con.close()

    return r is not None


def get_user(uid):

    con = db()
    cur = con.cursor()

    cur.execute("SELECT coins FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()

    if not r:

        cur.execute(
            "INSERT INTO users VALUES(?,?)",
            (uid, START_COINS)
        )

        con.commit()
        coins = START_COINS

    else:
        coins = r[0]

    con.close()

    return coins


def set_coins(uid, coins):

    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET coins=? WHERE user_id=?",
        (coins, uid)
    )

    con.commit()
    con.close()


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    coins = get_user(uid)

    await update.message.reply_text(
        f"🤖 Welcome!\n\n"
        f"💰 Coins: {coins}\n\n"
        "/store - Store\n"
        "/summon - Gacha\n"
        "/inv - Inventory\n"
        "/bal - Balance\n"
        "/rank - Ranking"
    )


# ================= BAL =================

async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    coins = get_user(update.effective_user.id)

    await update.message.reply_text(
        f"💳 Balance: {coins}"
    )


# ================= RANK =================

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT user_id,coins
    FROM users
    ORDER BY coins DESC
    LIMIT 10
    """)

    data = cur.fetchall()
    con.close()

    if not data:
        await update.message.reply_text("No ranking data")
        return

    text = "🏆 TOP 10 RANKING 🏆\n\n"

    for i, (uid, coins) in enumerate(data, 1):

        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = "Unknown"

        text += f"{i}. {name} — 💰 {coins}\n"

    await update.message.reply_text(text)


# ================= PHOTO UPLOAD =================

async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if not is_admin(uid):
        return

    if not update.message.photo:
        return

    caption = update.message.caption or ""
    parts = [p.strip() for p in caption.split("|")]

    name = parts[0] if len(parts) >= 1 and parts[0] else "Unknown"
    rarity = parts[1].capitalize() if len(parts) >= 2 else "Common"
    price = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 100
    faction = parts[3] if len(parts) >= 4 else "Unknown"

    file_id = update.message.photo[-1].file_id

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO characters(name,rarity,price,faction,file_id)
    VALUES(?,?,?,?,?)
    """, (name, rarity, price, faction, file_id))

    con.commit()
    con.close()

    await update.message.reply_text("✅ Character Saved")


# ================= STORE =================

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    con = db()
    cur = con.cursor()

    cur.execute("SELECT * FROM characters")
    chars = cur.fetchall()

    con.close()

    if not chars:
        await update.message.reply_text("Store empty")
        return

    STORE_CACHE[uid] = chars

    await show_store(update, context, uid, 0)


async def show_store(update, context, uid, index):

    chars = STORE_CACHE.get(uid)

    if not chars:
        return

    if index >= len(chars):
        index = 0

    if index < 0:
        index = len(chars) - 1

    char = chars[index]

    cid, name, rarity, price, faction, file_id = char

    text = (
        f"{RARITY_EMOJI.get(rarity,'❓')} *{name}*\n"
        f"⭐ {rarity}\n"
        f"💰 {price}\n"
        f"🏷 {faction}\n\n"
        f"{index+1}/{len(chars)}"
    )

    kb = [
        [
            InlineKeyboardButton("⬅️ Prev", callback_data=f"prev_{index}"),
            InlineKeyboardButton("➡️ Next", callback_data=f"next_{index}")
        ],
        [
            InlineKeyboardButton("🛒 Buy", callback_data=f"buy_{cid}")
        ]
    ]

    if update.callback_query:

        media = InputMediaPhoto(
            media=file_id,
            caption=text,
            parse_mode="Markdown"
        )

        await update.callback_query.edit_message_media(
            media=media,
            reply_markup=InlineKeyboardMarkup(kb)
        )

    else:

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=file_id,
            caption=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )


# ================= BUY =================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE, cid):

    q = update.callback_query
    uid = q.from_user.id

    coins = get_user(uid)

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT price FROM characters WHERE id=?",
        (cid,)
    )

    r = cur.fetchone()

    if not r:
        await q.answer("Invalid")
        return

    price = r[0]

    if coins < price:
        await q.answer("Not enough coins")
        return

    set_coins(uid, coins - price)

    cur.execute("""
    INSERT INTO inventory(user_id,char_id)
    VALUES(?,?)
    """, (uid, cid))

    con.commit()
    con.close()

    await q.edit_message_caption("✅ Purchased!")


# ================= INVENTORY =================

async def inv(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
        await update.message.reply_text("Inventory empty")
        return

    text = "📦 Inventory\n\n"

    for i, (name, rarity) in enumerate(items, 1):

        text += f"{i}. {RARITY_EMOJI[rarity]} {name}\n"

    await update.message.reply_text(text)


# ================= GACHA =================

def roll_rarity():

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

    if coins < SUMMON_COST:
        await update.message.reply_text("Not enough coins")
        return

    rarity = roll_rarity()

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM characters WHERE rarity=?",
        (rarity,)
    )

    chars = cur.fetchall()

    if not chars:
        await update.message.reply_text("No characters")
        return

    char = random.choice(chars)

    set_coins(uid, coins - SUMMON_COST)

    cur.execute("""
    INSERT INTO inventory(user_id,char_id)
    VALUES(?,?)
    """, (uid, char[0]))

    con.commit()
    con.close()

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=char[5],
        caption=f"🎲 Summoned {char[1]} ({rarity})"
    )


# ================= ADMIN =================

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("/add_admin user_id")
        return

    target = int(context.args[0])

    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO admins VALUES(?)",
        (target,)
    )

    con.commit()
    con.close()

    await update.message.reply_text("Admin Added")


async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("/remove_admin user_id")
        return

    target = int(context.args[0])

    con = db()
    cur = con.cursor()

    cur.execute(
        "DELETE FROM admins WHERE user_id=?",
        (target,)
    )

    con.commit()
    con.close()

    await update.message.reply_text("Admin Removed")


async def give_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    if len(context.args) != 2:
        await update.message.reply_text("/give_coin user_id amount")
        return

    target = int(context.args[0])
    amount = int(context.args[1])

    coins = get_user(target)

    set_coins(target, coins + amount)

    await update.message.reply_text("Coins Given")


# ================= BUTTON =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if data.startswith("buy_"):

        cid = int(data.split("_")[1])
        await buy(update, context, cid)

    elif data.startswith("next_"):

        i = int(data.split("_")[1]) + 1
        await show_store(update, context, uid, i)

    elif data.startswith("prev_"):

        i = int(data.split("_")[1]) - 1
        await show_store(update, context, uid, i)


# ================= MAIN =================

def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("inv", inv))
    app.add_handler(CommandHandler("summon", summon))

    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("remove_admin", remove_admin))
    app.add_handler(CommandHandler("give_coin", give_coin))

    app.add_handler(MessageHandler(filters.PHOTO, save_photo))

    app.add_handler(CallbackQueryHandler(buttons))

    logger.info("Bot Started")

    app.run_polling()


if __name__ == "__main__":
    main()
