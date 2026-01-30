import os
import json
import random
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

import aiosqlite

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = list(
    map(int, os.getenv("ADMIN_IDS", "").split(","))
)

DB_FILE = "bot.db"
CHAR_FILE = "characters.json"

MAX_DAILY = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ================= RARITY =================

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


# ================= DATABASE =================

async def init_db():

    async with aiosqlite.connect(DB_FILE) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id TEXT PRIMARY KEY,
            coins INTEGER,
            banned INTEGER DEFAULT 0,
            last_bonus TEXT,
            streak INTEGER,
            daily_count INTEGER,
            daily_date TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS cards(
            user_id TEXT,
            char_id TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS fav(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            rarity TEXT,
            image_url TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT,
            action TEXT,
            target TEXT,
            amount TEXT,
            date TEXT
        )
        """)

        await db.commit()


# ================= UTILS =================

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def roll_rarity():

    r = random.randint(1, 100)
    s = 0

    for k, v in RARITY_CHANCE.items():
        s += v

        if r <= s:
            return k

    return "Common"


async def get_user(uid: str):

    async with aiosqlite.connect(DB_FILE) as db:

        cur = await db.execute(
            "SELECT * FROM users WHERE user_id=?",
            (uid,)
        )

        user = await cur.fetchone()

        if not user:

            await db.execute("""
            INSERT INTO users
            (user_id, coins, banned, last_bonus, streak,
             daily_count, daily_date)
            VALUES (?, ?, 0, '', 0, 0, '')
            """, (uid, 500))

            await db.commit()

            return {
                "coins": 500,
                "banned": 0,
                "last_bonus": "",
                "streak": 0,
                "daily_count": 0,
                "daily_date": ""
            }

        return {
            "coins": user[1],
            "banned": user[2],
            "last_bonus": user[3],
            "streak": user[4],
            "daily_count": user[5],
            "daily_date": user[6]
        }


async def update_user(uid: str, data: Dict):

    async with aiosqlite.connect(DB_FILE) as db:

        await db.execute("""
        UPDATE users SET
        coins=?,
        banned=?,
        last_bonus=?,
        streak=?,
        daily_count=?,
        daily_date=?
        WHERE user_id=?
        """, (
            data["coins"],
            data["banned"],
            data["last_bonus"],
            data["streak"],
            data["daily_count"],
            data["daily_date"],
            uid
        ))

        await db.commit()


async def reset_daily(user: Dict):

    today = datetime.now().strftime("%Y-%m-%d")

    if user["daily_date"] != today:

        user["daily_date"] = today
        user["daily_count"] = 0


async def log_action(admin, action, target="", amount=""):

    async with aiosqlite.connect(DB_FILE) as db:

        await db.execute("""
        INSERT INTO logs
        (admin_id, action, target, amount, date)
        VALUES (?, ?, ?, ?, ?)
        """, (
            admin, action, target, amount,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))

        await db.commit()


# ================= CORE =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    user = await get_user(uid)

    if user["banned"]:
        return

    await reset_daily(user)
    await update_user(uid, user)

    text = (
        "🌌 Gacha World\n\n"
        f"💰 Coins: {user['coins']}\n"
        f"📦 Today: {user['daily_count']}/{MAX_DAILY}\n"
        f"🔥 Streak: {user['streak']}"
    )

    kb = [
        [InlineKeyboardButton("🛒 Store", callback_data="store")],
        [InlineKeyboardButton("🎁 Bonus", callback_data="bonus")],
        [InlineKeyboardButton("💳 Balance", callback_data="bal")],
        [InlineKeyboardButton("⭐ Fav", callback_data="fav_list")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= STORE =================

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    user = await get_user(uid)

    if user["banned"]:
        return

    await reset_daily(user)

    if user["daily_count"] >= MAX_DAILY:

        await update.effective_message.reply_text("❌ Limit reached")
        return

    with open(CHAR_FILE, encoding="utf-8") as f:
        chars = json.load(f)

    rarity = roll_rarity()

    pool = [c for c in chars if c["rarity"] == rarity]

    if not pool:

        await update.effective_message.reply_text("No items")
        return

    char = random.choice(pool)

    text = (
        f"{RARITY_EMOJI[rarity]} {char['name']} ({rarity})\n"
        f"💰 {char['price']}"
    )

    kb = [
        [InlineKeyboardButton("Buy", callback_data=f"buy_{char['id']}")],
        [InlineKeyboardButton("Next", callback_data="store")]
    ]

    if char.get("image_url"):

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=char["image_url"],
            caption=text,
            reply_markup=InlineKeyboardMarkup(kb)
        )

    else:

        await update.effective_message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(kb)
        )


# ================= BUY =================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)

    user = await get_user(uid)

    if user["banned"]:
        return

    await reset_daily(user)

    cid = q.data.split("_")[1]

    with open(CHAR_FILE, encoding="utf-8") as f:
        chars = json.load(f)

    char = next((c for c in chars if str(c["id"]) == cid), None)

    if not char:
        return

    if user["coins"] < char["price"]:

        await q.edit_message_text("❌ Not enough coins")
        return

    async with aiosqlite.connect(DB_FILE) as db:

        cur = await db.execute("""
        SELECT * FROM cards
        WHERE user_id=? AND char_id=?
        """, (uid, cid))

        owned = await cur.fetchone()

        if owned:

            await q.edit_message_text("Already owned")
            return

        await db.execute("""
        INSERT INTO cards(user_id, char_id)
        VALUES (?,?)
        """, (uid, cid))

        await db.commit()

    user["coins"] -= char["price"]
    user["daily_count"] += 1

    await update_user(uid, user)

    await q.edit_message_text(
        f"✅ Bought {char['name']}"
    )


# ================= BONUS =================

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    user = await get_user(uid)

    if user["banned"]:
        return

    today = datetime.now().strftime("%Y-%m-%d")

    if user["last_bonus"] == today:

        await update.message.reply_text("Already claimed")
        return

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if user["last_bonus"] == yesterday:
        user["streak"] += 1
    else:
        user["streak"] = 1

    reward = 50 + user["streak"] * 10

    user["coins"] += reward
    user["last_bonus"] = today

    await update_user(uid, user)

    await update.message.reply_text(
        f"🎁 +{reward} coins"
    )


# ================= BAL =================

async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    user = await get_user(uid)

    if user["banned"]:
        return

    await reset_daily(user)
    await update_user(uid, user)

    text = (
        "💳 Balance\n\n"
        f"Coins: {user['coins']}\n"
        f"Streak: {user['streak']}\n"
        f"Today: {user['daily_count']}/{MAX_DAILY}"
    )

    await update.message.reply_text(text)


# ================= FAVORITE =================

async def save_fav(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.photo:
        return

    uid = str(update.effective_user.id)

    user = await get_user(uid)

    if user["banned"]:
        return

    cap = update.message.caption or ""

    if not cap.lower().startswith("fav |"):
        return

    parts = [p.strip() for p in cap.split("|")]

    if len(parts) < 3:
        return

    name = parts[1]
    rarity = parts[2]

    file_id = update.message.photo[-1].file_id

    file = await context.bot.get_file(file_id)

    url = file.file_path

    async with aiosqlite.connect(DB_FILE) as db:

        await db.execute("""
        INSERT INTO fav(user_id,name,rarity,image_url)
        VALUES (?,?,?,?)
        """, (uid, name, rarity, url))

        await db.commit()

    await update.message.reply_text("⭐ Saved")


async def fav_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = str(update.effective_user.id)

    async with aiosqlite.connect(DB_FILE) as db:

        cur = await db.execute("""
        SELECT id,name,rarity FROM fav
        WHERE user_id=?
        """, (uid,))

        rows = await cur.fetchall()

    if not rows:

        await update.message.reply_text("No fav")
        return

    text = "⭐ Favorites\n\n"

    for r in rows:
        text += f"{r[0]}. {r[1]} ({r[2]})\n"

    await update.message.reply_text(text)


async def fav_show(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        return

    fid = context.args[0]

    uid = str(update.effective_user.id)

    async with aiosqlite.connect(DB_FILE) as db:

        cur = await db.execute("""
        SELECT name,rarity,image_url
        FROM fav WHERE id=? AND user_id=?
        """, (fid, uid))

        row = await cur.fetchone()

    if not row:

        await update.message.reply_text("Invalid ID")
        return

    await update.message.reply_photo(
        photo=row[2],
        caption=f"{row[0]} ({row[1]})"
    )


# ================= ADMIN =================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    kb = [
        [InlineKeyboardButton("💰 Give Coin", callback_data="ad_coin")],
        [InlineKeyboardButton("🎴 Give Char", callback_data="ad_char")],
        [InlineKeyboardButton("🚫 Ban", callback_data="ad_ban")],
        [InlineKeyboardButton("✅ Unban", callback_data="ad_unban")],
        [InlineKeyboardButton("📜 Logs", callback_data="ad_logs")]
    ]

    await update.message.reply_text(
        "🛠 Admin Panel",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if not is_admin(uid):
        return

    d = q.data

    if d == "ad_coin":
        await q.message.reply_text("/give_coin user_id amount")

    elif d == "ad_char":
        await q.message.reply_text("/give_char user_id char_id")

    elif d == "ad_ban":
        await q.message.reply_text("/ban user_id")

    elif d == "ad_unban":
        await q.message.reply_text("/unban user_id")

    elif d == "ad_logs":
        await show_logs(q.message)


async def show_logs(msg):

    async with aiosqlite.connect(DB_FILE) as db:

        cur = await db.execute("""
        SELECT admin_id,action,target,amount,date
        FROM logs ORDER BY id DESC LIMIT 10
        """)

        rows = await cur.fetchall()

    if not rows:
        await msg.reply_text("No logs")
        return

    text = "📜 Logs\n\n"

    for r in rows:
        text += f"{r[4]} | {r[1]} | {r[2]} | {r[3]}\n"

    await msg.reply_text(text)


# ================= ADMIN COMMAND =================

async def give_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    uid = context.args[0]
    amt = int(context.args[1])

    user = await get_user(uid)

    user["coins"] += amt

    await update_user(uid, user)

    await log_action(
        update.effective_user.id,
        "give_coin",
        uid,
        amt
    )

    await update.message.reply_text("Done")


async def give_char(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    uid = context.args[0]
    cid = context.args[1]

    async with aiosqlite.connect(DB_FILE) as db:

        await db.execute("""
        INSERT INTO cards(user_id,char_id)
        VALUES (?,?)
        """, (uid, cid))

        await db.commit()

    await log_action(
        update.effective_user.id,
        "give_char",
        uid,
        cid
    )

    await update.message.reply_text("Done")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    uid = context.args[0]

    user = await get_user(uid)

    user["banned"] = 1

    await update_user(uid, user)

    await log_action(
        update.effective_user.id,
        "ban",
        uid
    )

    await update.message.reply_text("Banned")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return

    uid = context.args[0]

    user = await get_user(uid)

    user["banned"] = 0

    await update_user(uid, user)

    await log_action(
        update.effective_user.id,
        "unban",
        uid
    )

    await update.message.reply_text("Unbanned")


# ================= MAIN =================

def main():

    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    asyncio.run(init_db())

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("bonus", bonus))

    # Fav
    app.add_handler(MessageHandler(filters.PHOTO, save_fav))
    app.add_handler(CommandHandler("fav_list", fav_list))
    app.add_handler(CommandHandler("fav_show", fav_show))

    # Admin
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("give_coin", give_coin))
    app.add_handler(CommandHandler("give_char", give_char))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))

    app.add_handler(CallbackQueryHandler(admin_button, pattern="^ad_"))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(store, pattern="^store$"))

    print("🤖 Bot Started")

    app.run_polling()


if __name__ == "__main__":
    main()
