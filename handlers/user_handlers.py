# handlers/user_handlers.py
import random
from datetime import datetime
from typing import List

from telegram import Update
from telegram.ext import ContextTypes
from utils.translate_utils import auto_translate

import config
from utils.json_utils import load_json, save_json
from utils.bot_utils import broadcast_to_chats

USERS_FILE = getattr(config, "USERS_FILE", "data/users.json")
VERSES_FILE = getattr(config, "VERSES_FILE", "data/verses.json")
EVENTS_FILE = getattr(config, "EVENTS_FILE", "data/events.json")
GROUPS_FILE = getattr(config, "GROUPS_FILE", "data/groups.json")

def _format_name(user):
    return f"{user.first_name or ''} {user.last_name or ''}".strip()

async def add_user(uid: int, username: str = None, name: str = None):
    users = await load_json(USERS_FILE, {})
    uid_s = str(uid)
    if uid_s not in users:
        users[uid_s] = {
            "username": username,
            "full_name": name,
            "quiz_score": 0,
            "prayer_requests": [],
            "first_seen": datetime.utcnow().isoformat(),
        }
    else:
        users[uid_s]["username"] = username
        users[uid_s]["full_name"] = name
    await save_json(USERS_FILE, users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    name = _format_name(u)
    await add_user(u.id, u.username, name)

    # persist group id if group
    if update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
        groups = await load_json(GROUPS_FILE, [])
        gid = update.effective_chat.id
        if gid not in groups:
            groups.append(gid)
            await save_json(GROUPS_FILE, groups)

    msg = (
        "🙌 Welcome!\n\n"
        "This is Church Community Bot.\n"
        "Type /cmd to see commands."
    )
    await update.message.reply_text(msg)

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
"/start - Register\n"
"/cmd - All commands\n"
"/verse - Random verse\n"
"/prayer <text> - Prayer\n"
"/events - Events\n"
"/quiz - Quiz\n"
"/tops - Ranking\n"
"/daily_inspiration - Daily Word\n"
"/myid - Show your Telegram ID\n"
"/chatid - Show current chat ID\n"
"/broadcast <message> - Send to configured groups (Admin)\n"
"/broadcast_users <message> - Send DM to all saved users (Admin)\n"
"/addadmin <user_id> - Add admin (Admin)\n"
"/listadmins - Show admin list (Admin)\n"
"/deladmin <user_id> - Remove admin (Admin)\n"
    )
    await update.message.reply_text(text)

async def verse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await load_json(VERSES_FILE, [])
    if not data:
        await update.message.reply_text("No verses yet.")
        return
    await update.message.reply_text("📖 " + random.choice(data))

async def prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /prayer <text>")
        return
    u = update.effective_user
    await add_user(u.id, u.username, u.first_name)
    users = await load_json(USERS_FILE, {})
    uid = str(u.id)
    text = " ".join(context.args)
    users[uid]["prayer_requests"].append({
        "text": text,
        "time": datetime.utcnow().isoformat()
    })
    await save_json(USERS_FILE, users)
    await update.message.reply_text("🙏 Prayer saved.")

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await load_json(EVENTS_FILE, [])
    if not data:
        await update.message.reply_text("No events.")
        return
    msg = "🗓 EVENTS\n\n"
    for e in data:
        msg += f"{e.get('name')} - {e.get('time')}\n"
    await update.message.reply_text(msg)

async def tops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = await load_json(USERS_FILE, {})
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

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = [
        "Trust in the Lord. 🙏",
        "God is with you. ✨",
        "Keep praying. 💙",
        "Faith over fear. 🌟",
        "Jesus loves you. ❤️",
    ]
    await update.message.reply_text(random.choice(data))

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uname = update.effective_user.username
    text = f"🆔 Your ID: {uid}\n👤 Username: @{uname}" if uname else f"🆔 Your ID: {uid}"
    await update.message.reply_text(text)

async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ctype = update.effective_chat.type
    await update.message.reply_text(f"🆔 Chat ID: {cid}\n📌 Type: {ctype}")




async def tran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /auto_translate <text>")
        return
    
    text = " ".join(context.args)
    # Detect language automatically and translate to opposite (Myanmar ↔ English)
    # Simple logic: if contains Myanmar unicode, translate to English; else to Myanmar
    if any("\u1000" <= ch <= "\u109F" for ch in text):  # Myanmar unicode range
        translated = auto_translate(text, src="my", dest="en")
    else:
        translated = auto_translate(text, src="en", dest="my")
    
    await update.message.reply_text(translated)

