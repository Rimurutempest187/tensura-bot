import logging
import inspect
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import config
from utils.json_utils import load_json
from utils.bot_utils import broadcast_to_chats

logger = logging.getLogger(__name__)

GROUPS_FILE = getattr(config, "GROUPS_FILE", "data/groups.json")
USERS_FILE = getattr(config, "USERS_FILE", "data/users.json")


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


async def _load_persisted_groups():
    data = await _maybe_await(load_json(GROUPS_FILE, []))
    if isinstance(data, dict) and "groups" in data:
        data = data.get("groups", [])
    if not isinstance(data, list):
        return []
    out = []
    for x in data:
        try:
            out.append(int(x))
        except Exception:
            logger.warning("Invalid group id in %s: %s", GROUPS_FILE, x)
    return list(dict.fromkeys(out))


async def _load_users_list():
    data = await _maybe_await(load_json(USERS_FILE, {}))
    if isinstance(data, dict):
        ids = []
        for k in data.keys():
            try:
                ids.append(int(k))
            except Exception:
                logger.warning("Invalid user id in %s: %s", USERS_FILE, k)
        return ids
    return []


async def _direct_broadcast(bot, message, chat_ids, delay_ms=200):
    ok = 0
    fail = 0
    for cid in chat_ids:
        try:
            await bot.send_message(chat_id=cid, text=message)
            ok += 1
            if delay_ms:
                await asyncio.sleep(delay_ms / 1000.0)
        except Exception as e:
            logger.exception("Direct send failed to %s: %s", cid, e)
            fail += 1
    return ok, fail


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        from handlers.admin_handlers import is_admin
        if not is_admin(user.id):
            await update.message.reply_text("❌ Not authorized.")
            return
    except Exception:
        logger.debug("is_admin not available; skipping admin check")

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)

    configured = getattr(config, "GROUP_IDS", []) or []
    try:
        configured = [int(x) for x in configured]
    except Exception:
        configured = []

    persisted = await _load_persisted_groups()
    all_ids = list(dict.fromkeys(configured + persisted))
    if not all_ids:
        await update.message.reply_text("⚠️ No target groups configured.")
        return

    await update.message.reply_text(f"📤 Broadcasting to {len(all_ids)} groups...")

    try:
        result = broadcast_to_chats(context.bot, message, all_ids)
        result = await _maybe_await(result)
        if isinstance(result, tuple) and len(result) == 2:
            ok, fail = result
        else:
            logger.warning("broadcast_to_chats returned unexpected value: %s", result)
            ok, fail = await _direct_broadcast(context.bot, message, all_ids)
    except Exception as e:
        logger.exception("broadcast_to_chats failed: %s", e)
        ok, fail = await _direct_broadcast(context.bot, message, all_ids)

    await update.message.reply_text(f"✅ Broadcast to groups completed. Sent: {ok}, Failed: {fail}")


async def broadcast_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        from handlers.admin_handlers import is_admin
        if not is_admin(user.id):
            await update.message.reply_text("❌ Not authorized.")
            return
    except Exception:
        logger.debug("is_admin not available; skipping admin check")

    if not context.args:
        await update.message.reply_text("Usage: /broadcast_users <message>")
        return

    message = " ".join(context.args)

    user_ids = await _load_users_list()
    if not user_ids:
        await update.message.reply_text("⚠️ No users found to broadcast to.")
        return

    await update.message.reply_text(f"📤 Broadcasting to {len(user_ids)} users...")

    try:
        result = broadcast_to_chats(context.bot, message, user_ids)
        result = await _maybe_await(result)
        if isinstance(result, tuple) and len(result) == 2:
            ok, fail = result
        else:
            logger.warning("broadcast_to_chats returned unexpected value: %s", result)
            ok, fail = await _direct_broadcast(context.bot, message, user_ids)
    except Exception as e:
        logger.exception("broadcast_to_chats failed: %s", e)
        ok, fail = await _direct_broadcast(context.bot, message, user_ids)

    await update.message.reply_text(f"✅ Broadcast to users completed. Sent: {ok}, Failed: {fail}")
