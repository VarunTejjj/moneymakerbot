import asyncio
import os
import time
import datetime
import json
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.dispatcher.filters import Command

from config import BOT_TOKEN, UPI_ID, UPI_NAME, KEY_VALIDITY_DAYS
from screenshot_checker import check_screenshot
from subscription import generate_key

logging.basicConfig(level=logging.INFO)

SUBS_FILE = "subscriptions.json"
ADMIN_IDS = [1831313735]

PUBLIC_CHANNEL_ID = -1002800054599
PUBLIC_CHANNEL_LINK = "https://t.me/anythinghere07"
FORCE_GROUP_ID = -1002718775143
FORCE_GROUP_LINK = "https://t.me/+37DfTLNkfcwwZDhl"
PREMIUM_CHANNEL_ID = -1002731631370

session_messages = {}

def load_subscriptions():
    try:
        with open(SUBS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_subscriptions(subs):
    with open(SUBS_FILE, 'w') as f:
        json.dump(subs, f)

def get_user_record(user_id):
    subs = load_subscriptions()
    return subs.get(str(user_id), {})

def get_user_expiry(user_id):
    record = get_user_record(user_id)
    return record.get("expiry", 0)

def get_user_key(user_id):
    record = get_user_record(user_id)
    return record.get("key", None)

def get_user_name(user_id):
    record = get_user_record(user_id)
    return record.get("name", "Unknown")

def set_user_subscription(user_id, key, expiry, name):
    subs = load_subscriptions()
    subs[str(user_id)] = {"key": key, "expiry": expiry, "name": name}
    save_subscriptions(subs)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def is_member(bot, user_id, chat_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

def premium_menu(user_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("💳 Take Subscription", callback_data="subscribe")],
        [InlineKeyboardButton("👁️‍🗨️ See Premium Features", callback_data="see_features")]
    ])

def force_join_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Join Channel 📢", url=PUBLIC_CHANNEL_LINK)],
        [InlineKeyboardButton("Join Group 💬", url=FORCE_GROUP_LINK)],
        [InlineKeyboardButton("✅ I joined", callback_data="check_join")]
    ])

def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
    ])

async def delete_single_message_safe(chat_id, message_id):
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

async def delete_messages_list(chat_id, message_ids):
    for mid in message_ids:
        await delete_single_message_safe(chat_id, mid)

@dp.message_handler(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    session_messages[user_id] = {}
    in_channel = await is_member(bot, user_id, PUBLIC_CHANNEL_ID)
    in_group = await is_member(bot, user_id, FORCE_GROUP_ID)
    if not in_channel or not in_group:
        sent = await message.answer(
            "🚀 To continue, join BOTH our official channel and group:\n\n"
            f"1️⃣ [Join Channel]({PUBLIC_CHANNEL_LINK})\n"
            f"2️⃣ [Join Group]({FORCE_GROUP_LINK})\n\n"
            "After joining both, tap '✅ I joined' below.",
            parse_mode="Markdown",
            reply_markup=force_join_menu()
        )
        session_messages[user_id]['menu'] = sent.message_id
        session_messages[user_id]['start_cmd'] = message.message_id
        return
    name = message.from_user.first_name or "there"
    expiry = get_user_expiry(user_id)
    now = int(time.time())
    if expiry > now:
        sent = await message.answer(
            f"🏆 Hi {name}!\n"
            "<b>Welcome to MoneyMaker Premium! 🚀</b>\n\n"
            "<code>✨ PREMIUM SUBSCRIBER</code> ✅\n\n"
            "Thank you for being a valued member! Your subscription is <b>active</b>.\n"
            "Use <b>/premem</b> anytime to view your subscription details and key.",
            parse_mode="HTML"
        )
        session_messages[user_id]['menu'] = sent.message_id
        session_messages[user_id]['start_cmd'] = message.message_id
    else:
        sent = await message.answer(
            f"👋 Hi <b>{name}</b>!\n"
            "Welcome to MoneyMaker Premium! 🚀\n\n"
            "Unlock exclusive tips, signals, and more.",
            parse_mode="HTML",
            reply_markup=premium_menu(name)
        )
        session_messages[user_id]['menu'] = sent.message_id
        session_messages[user_id]['start_cmd'] = message.message_id

@dp.callback_query_handler(lambda c: c.data == "check_join")
async def check_join(call: CallbackQuery):
    user_id = call.from_user.id
    in_channel = await is_member(bot, user_id, PUBLIC_CHANNEL_ID)
    in_group = await is_member(bot, user_id, FORCE_GROUP_ID)
    await delete_single_message_safe(call.message.chat.id, call.message.message_id)
    name = call.from_user.first_name or "there"
    user_id = call.from_user.id
    expiry = get_user_expiry(user_id)
    now = int(time.time())
    if in_channel and in_group:
        if expiry > now:
            sent = await call.message.answer(
                f"🏆 Hi {name}!\n"
                "<b>Welcome to MoneyMaker Premium! 🚀</b>\n\n"
                "<code>✨ PREMIUM SUBSCRIBER</code> ✅\n\n"
                "Thank you for being a valued member! Your subscription is <b>active</b>.\n"
                "Use <b>/premem</b> anytime to view your subscription details and key.",
                parse_mode="HTML"
            )
            session_messages[user_id]['menu'] = sent.message_id
        else:
            sent = await call.message.answer(
                f"👋 Hi <b>{name}</b>!\n"
                "Welcome to MoneyMaker Premium! 🚀\n\n"
                "Unlock exclusive tips, signals, and more.",
                parse_mode="HTML",
                reply_markup=premium_menu(name)
            )
            session_messages[user_id]['menu'] = sent.message_id
    else:
        sent = await call.message.answer(
            "❗ You must join both the channel and group to continue.",
            reply_markup=force_join_menu()
        )
        session_messages[user_id]['menu'] = sent.message_id

@dp.callback_query_handler(lambda c: c.data == "see_features")
async def see_features(call: CallbackQuery):
    await delete_single_message_safe(call.message.chat.id, call.message.message_id)
    sent = await call.message.answer(
        "Hello thier",
        reply_markup=back_button()
    )
    session_messages[call.from_user.id]['features'] = sent.message_id

@dp.callback_query_handler(lambda c: c.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery):
    await delete_single_message_safe(call.message.chat.id, call.message.message_id)
    user_id = call.from_user.id
    if 'features' in session_messages.get(user_id, {}):
        name = call.from_user.first_name or "there"
        expiry = get_user_expiry(user_id)
        now = int(time.time())
        if expiry > now:
            sent = await call.message.answer(
                f"🏆 Hi {name}!\n"
                "<b>Welcome to MoneyMaker Premium! 🚀</b>\n\n"
                "<code>✨ PREMIUM SUBSCRIBER</code> ✅\n\n"
                "Thank you for being a valued member! Your subscription is <b>active</b>.\n"
                "Use <b>/premem</b> anytime to view your subscription details and key.",
                parse_mode="HTML"
            )
        else:
            sent = await call.message.answer(
                f"👋 Hi <b>{name}</b>!\n"
                "Welcome to MoneyMaker Premium! 🚀\n\n"
                "Unlock exclusive tips, signals, and more.",
                parse_mode="HTML",
                reply_markup=premium_menu(name)
            )
        session_messages[user_id]['menu'] = sent.message_id
        session_messages[user_id].pop('features', None)

@dp.callback_query_handler(lambda c: c.data == "subscribe")
async def subscribe_instruction(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    now = int(time.time())
    expiry = get_user_expiry(user_id)
    key = get_user_key(user_id)
    if expiry > now and key:
        record = get_user_record(user_id)
        name = record.get("name", call.from_user.first_name or "Unknown")
        expiry_str = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        purchase_str = datetime.datetime.fromtimestamp(expiry - KEY_VALIDITY_DAYS * 24 * 60 * 60).strftime('%Y-%m-%d %H:%M:%S')
        sent = await call.message.answer(
            f"🟢 <b>You have an active subscription!</b>\n\n"
            f"<b>Name:</b> {name}\n"
            f"<b>Key:</b> <code>{key}</code>\n"
            f"<b>Purchased:</b> {purchase_str}\n"
            f"<b>Expires:</b> {expiry_str}",
            parse_mode="HTML"
        )
        session_messages[user_id]['menu'] = sent.message_id
    else:
        instr = await call.message.answer(
            f"To get <b>7 days of premium access</b>:\n\n"
            f"💸 <b>Pay ₹5</b> UPI: <code>{UPI_ID}</code>\n"
            f"Name: <b>{UPI_NAME}</b>\n\n"
            "Then send your payment screenshot here.",
            parse_mode="HTML"
        )
        session_messages.setdefault(user_id, {})['payment'] = instr.message_id

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    session_messages.setdefault(user_id, {})['screenshot'] = message.message_id
    in_channel = await is_member(bot, user_id, PUBLIC_CHANNEL_ID)
    in_group = await is_member(bot, user_id, FORCE_GROUP_ID)
    if not in_channel or not in_group:
        sent = await message.answer(
            "❗ You must join both the channel and group before sending a screenshot.",
            reply_markup=force_join_menu()
        )
        session_messages[user_id]['menu'] = sent.message_id
        return
    checking_msg = await message.answer("🔎 Checking your payment screenshot...")
    session_messages[user_id]['checking'] = checking_msg.message_id

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    image_data = await bot.download_file(file_path)
    tmp_path = f"{user_id}_screenshot.jpg"
    with open(tmp_path, "wb") as f:
        f.write(image_data.read())
    try:
        if check_screenshot(tmp_path):
            key = generate_key()
            now = int(time.time())
            expiry = now + KEY_VALIDITY_DAYS * 24 * 60 * 60
            name = message.from_user.first_name or "Unknown"
            set_user_subscription(user_id, key, expiry, name)
            try:
                await bot.send_message(
                    chat_id=FORCE_GROUP_ID,
                    text=f"🌟 User <b>{name}</b> (ID: <code>{user_id}</code>) just unlocked MoneyMaker Premium! 🎉\nWelcome to the VIP circle!",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            invite = await bot.create_chat_invite_link(
                chat_id=PREMIUM_CHANNEL_ID,
                member_limit=1,
                expire_date=now + 3600
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("📥 Join Private Channel", url=invite.invite_link)],
    [InlineKeyboardButton("🚀 Lets Start", callback_data="lets_start")]
])
            msg_ids = [v for k, v in session_messages[user_id].items() if k in ('menu', 'payment', 'checking', 'screenshot', 'start_cmd')]
            await delete_messages_list(message.chat.id, msg_ids)
            try:
                await bot.delete_message(message.chat.id, session_messages[user_id].get('start_cmd'))
            except Exception:
                pass
            await message.answer(
                f"✅ <b>Payment Verified!</b>\n\n"
                f"🔑 <b>Your Key:</b> <code>{key}</code>\n"
                "<i>Tap below for your single-use join link.</i>\n"
                "⚠️ <b>This link is only for you and will expire in 1 hour.</b>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            session_messages[user_id] = {}
        else:
            try:
                await bot.delete_message(message.chat.id, checking_msg.message_id)
            except Exception:
                pass
            await message.answer(
                "❌ <b>Screenshot is invalid.</b>\nPlease send a valid UPI payment screenshot.",
                parse_mode="HTML"
            )
    finally:
        os.remove(tmp_path)

@dp.message_handler(commands=["premem"])
async def premium_member(message: Message):
    try:
        history = [msg async for msg in bot.iter_history(message.chat.id, limit=2)]
        if len(history) == 2:
            prev_msg = history[1]
            await delete_single_message_safe(message.chat.id, prev_msg.message_id)
        await delete_single_message_safe(message.chat.id, message.message_id)
        return
    except Exception:
        pass
    user_id = message.from_user.id
    record = get_user_record(user_id)
    expiry = record.get("expiry", 0)
    key = record.get("key", None)
    now = int(time.time())
    if expiry > now and key:
        purchase_time = expiry - KEY_VALIDITY_DAYS * 24 * 60 * 60
        purchase_str = datetime.datetime.fromtimestamp(purchase_time).strftime('%Y-%m-%d %H:%M:%S')
        expiry_str = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        sent = await message.answer(
            "<b>👤 Premium Subscription Details</b>\n\n"
            f"<b>Purchase Date:</b> {purchase_str}\n"
            f"<b>Expiry Date:</b> {expiry_str}\n\n"
            f"<b>Your Key:</b> <span class=\"tg-spoiler\">{key}</span>",
            parse_mode="HTML",
            reply_markup=back_button()
        )
        session_messages[user_id]['premem'] = sent.message_id
    else:
        await message.answer(
            "❌ You are not a premium subscriber. Please subscribe to access premium features."
        )

@dp.message_handler(commands=["check"])
async def check_subscribers(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 You are not authorized to use this command.")
        return
    subs = load_subscriptions()
    if not subs:
        await message.reply("No users have taken the subscription yet.")
        return
    reply = "<b>Active Subscribers:</b>\n\n"
    now = int(time.time())
    for user_id, record in subs.items():
        expiry = record.get("expiry", 0)
        key = record.get("key", "N/A")
        name = record.get("name", "Unknown")
        if expiry > now:
            dt = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
            reply += (
                f"• <code>{user_id}</code> — <b>{name}</b> — "
                f"key: <code>{key}</code> — expires: <b>{dt}</b>\n"
            )
    await message.reply(reply, parse_mode="HTML")

@dp.message_handler(commands=["extend"])
async def extend_sub(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 You are not authorized to use this command.")
        return
    args = message.get_args().split()
    if len(args) != 2 or not args[1].isdigit():
        await message.reply("Usage: /extend <user_id> <days>")
        return
    user_id, days = args[0], int(args[1])
    subs = load_subscriptions()
    now = int(time.time())
    if user_id in subs:
        expiry = max(subs[user_id]["expiry"], now) + days * 86400
        key = subs[user_id]["key"]
        name = subs[user_id].get("name", "Unknown")
    else:
        key = generate_key()
        expiry = now + days * 86400
        name = "Unknown"
    subs[user_id] = {"key": key, "expiry": expiry, "name": name}
    save_subscriptions(subs)
    dt = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
    await message.reply(f"User {user_id}'s subscription now expires on {dt}.")

@dp.message_handler(commands=["revoke"])
async def revoke_sub(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 You are not authorized to use this command.")
        return
    args = message.get_args().split()
    if len(args) != 1:
        await message.reply("Usage: /revoke <user_id>")
        return
    user_id = args[0]
    subs = load_subscriptions()
    if user_id in subs:
        del subs[user_id]
        save_subscriptions(subs)
        try:
            await bot.kick_chat_member(PREMIUM_CHANNEL_ID, int(user_id))
            await bot.unban_chat_member(PREMIUM_CHANNEL_ID, int(user_id))
        except Exception:
            pass
        await message.reply(f"Revoked and removed user {user_id} from premium channel.")
    else:
        await message.reply("No such user in the subscription database.")

@dp.message_handler(commands=["status"])
async def admin_status(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("🚫 You are not authorized to use this command.")
        return
    subs = load_subscriptions()
    now = int(time.time())
    active = sum(1 for v in subs.values() if v["expiry"] > now)
    soon_exp = sorted([(uid, v["expiry"]) for uid, v in subs.items() if now < v["expiry"] < now + 3 * 86400], key=lambda x: x[1])
    expired = [uid for uid, v in subs.items() if v["expiry"] <= now]
    text = (f"👥 Active Premium: {active}\n"
            f"🔔 Expiring Soon:\n" +
            "".join(f"• {uid} — {datetime.datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M:%S')}\n" for uid, exp in soon_exp) +
            f"\n❌ Expired: {', '.join(expired) if expired else 'None'}")
    await message.reply(text)

async def remove_expired_users():
    while True:
        now = int(time.time())
        subs = load_subscriptions()
        updated = False
        for user_id, rec in list(subs.items()):
            if rec["expiry"] <= now:
                try:
                    await bot.kick_chat_member(PREMIUM_CHANNEL_ID, int(user_id))
                    await bot.unban_chat_member(PREMIUM_CHANNEL_ID, int(user_id))
                    await bot.send_message(int(user_id), "Your premium subscription has expired. Contact us anytime to renew!")
                except Exception:
                    pass
                del subs[user_id]
                updated = True
        if updated:
            save_subscriptions(subs)
        await asyncio.sleep(3600)

async def main():
    asyncio.create_task(remove_expired_users())
    logging.info("Bot is running.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
