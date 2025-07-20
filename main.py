import asyncio
import os
import time
import datetime
import json
import logging
import re

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.dispatcher.filters import Command

from config import BOT_TOKEN, UPI_ID, UPI_NAME, KEY_VALIDITY_DAYS
from screenshot_checker import check_screenshot
from subscription import generate_key

logging.basicConfig(level=logging.INFO)

SUBS_FILE = "subscriptions.json"
ADMIN_IDS = [1831313735]  # Your admin user ID

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

def set_user_subscription(user_id, key, expiry):
    subs = load_subscriptions()
    subs[str(user_id)] = {"key": key, "expiry": expiry}
    save_subscriptions(subs)

def escape_markdown(text):
    # Escapes all special MarkdownV2 characters
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(Command("start"))
async def start(message: Message):
    name = message.from_user.first_name or "there"
    expiry = get_user_expiry(message.from_user.id)
    now = int(time.time())
    if expiry > now:
        await message.answer(
            f"🏆 Hi {name}!\n"
            "<b>Welcome to MoneyMaker Premium! 🚀</b>\n\n"
            "<code>✨ PREMIUM SUBSCRIBER</code> ✅\n\n"
            "Thank you for being a valued member! Your subscription is <b>active</b>.\n"
            "Use <b>/premem</b> anytime to view your subscription details and key.",
            parse_mode="HTML"
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✨ Join Channel", url="https://t.me/+nkPAaWA1TI8xOTVl")],
            [InlineKeyboardButton("💳 Get Subscription", callback_data="subscribe")]
        ])
        await message.answer(
            f"👋 <b>Hi {name}!</b>\n"
            "<b>Welcome to MoneyMaker Premium! 🚀</b>\n\n"
            "Unlock exclusive tips, signals, and more.\n"
            "Press one of the buttons below to continue.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

@dp.callback_query_handler(lambda c: c.data == "subscribe")
async def subscribe_instruction(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    now = int(time.time())
    expiry = get_user_expiry(user_id)
    key = get_user_key(user_id)
    if expiry > now and key:
        expiry_str = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        purchase_str = datetime.datetime.fromtimestamp(expiry - KEY_VALIDITY_DAYS*24*60*60).strftime('%Y-%m-%d %H:%M:%S')
        await call.message.answer(
            f"🟢 <b>You have an active subscription!</b>\n\n"
            f"<b>Key:</b> <code>{key}</code>\n"
            f"<b>Purchased:</b> {purchase_str}\n"
            f"<b>Expires:</b> {expiry_str}",
            parse_mode="HTML"
        )
    else:
        await call.message.answer(
            f"To get <b>7 days of premium access</b>:\n\n"
            f"💸 <b>Pay ₹5</b> UPI: <code>{UPI_ID}</code>\n"
            f"Name: <b>{UPI_NAME}</b>\n\n"
            "Then send your payment screenshot here.",
            parse_mode="HTML"
        )

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: Message):
    await message.answer("🔎 Checking your payment screenshot...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    image_data = await bot.download_file(file_path)
    tmp_path = f"{message.from_user.id}_screenshot.jpg"
    with open(tmp_path, "wb") as f:
        f.write(image_data.read())
    try:
        if check_screenshot(tmp_path):
            key = generate_key()
            now = int(time.time())
            expiry = now + KEY_VALIDITY_DAYS * 24 * 60 * 60
            set_user_subscription(message.from_user.id, key, expiry)
            invite = await bot.create_chat_invite_link(
                chat_id=-1002731631370,
                member_limit=1,
                expire_date=now + 3600
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📥 Join Private Channel", url=invite.invite_link)]
            ])
            await message.answer(
                f"✅ <b>Payment Verified!</b>\n\n"
                f"🔑 <b>Your Key:</b> <code>{key}</code>\n"
                "<i>Tap below for your single-use join link.</i>\n"
                "⚠️ <b>This link is only for you and will expire in 1 hour.</b>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "❌ <b>Screenshot is invalid.</b>\nPlease send a valid UPI payment screenshot.",
                parse_mode="HTML"
            )
    finally:
        os.remove(tmp_path)

@dp.message_handler(commands=["premem"])
async def premium_member(message: Message):
    user_id = message.from_user.id
    record = get_user_record(user_id)
    expiry = record.get("expiry", 0)
    key = record.get("key", None)
    now = int(time.time())
    if expiry > now and key:
        purchase_time = expiry - KEY_VALIDITY_DAYS * 24 * 60 * 60
        purchase_str = datetime.datetime.fromtimestamp(purchase_time).strftime('%Y-%m-%d %H:%M:%S')
        expiry_str = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        key_md = escape_markdown(key)
        await message.answer(
            "<b>👤 Premium Subscription Details</b>\n\n"
            f"<b>Purchase Date:</b> {purchase_str}\n"
            f"<b>Expiry Date:</b> {expiry_str}\n\n"
            f"<b>Your Key:</b> ||{key_md}||",
            parse_mode="MarkdownV2"
        )
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
    active = 0
    for user_id, record in subs.items():
        expiry = record.get("expiry", 0)
        key = record.get("key", "N/A")
        if expiry > now:
            dt = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
            reply += f"• <code>{user_id}</code> — key: <code>{key}</code> — expires: <b>{dt}</b>\n"
            active += 1

    if active == 0:
        await message.reply("No active subscriptions found.", parse_mode="HTML")
    else:
        await message.reply(reply, parse_mode="HTML")

async def main():
    logging.info("Bot is running.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
