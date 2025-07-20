import asyncio
import os
import time
import datetime
import json
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Message, CallbackQuery
from aiogram.dispatcher.filters import Command

from config import BOT_TOKEN, UPI_ID, UPI_NAME, KEY_VALIDITY_DAYS
from screenshot_checker import check_screenshot
from subscription import generate_key

logging.basicConfig(level=logging.INFO)

SUBS_FILE = "subscriptions.json"

def load_subscriptions():
    try:
        with open(SUBS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_subscriptions(subs):
    with open(SUBS_FILE, 'w') as f:
        json.dump(subs, f)

def get_user_expiry(user_id):
    subs = load_subscriptions()
    return subs.get(str(user_id), 0)

def set_user_subscription(user_id, expiry):
    subs = load_subscriptions()
    subs[str(user_id)] = expiry
    save_subscriptions(subs)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(Command("start"))
async def start(message: Message):
    logging.info(f"/start called by {message.from_user.id}")
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Join Channel", url="https://t.me/+nkPAaWA1TI8xOTVl")],
            [InlineKeyboardButton(text="💳 Get Subscription", callback_data="subscribe")]
        ])
        await message.answer(
            "<b>Welcome to MoneyMaker Premium! 🚀</b>\n\n"
            "Unlock exclusive tips, signals, and more.\n"
            "Press one of the buttons below to continue.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Error in /start: {e}")
        await message.answer("⚠️ An error occurred while starting. Please try again later.")

@dp.callback_query_handler(lambda c: c.data == "subscribe")
async def subscribe_instruction(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    now = int(time.time())
    expiry = get_user_expiry(user_id)
    if expiry > now:
        expiry_str = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        await call.message.answer(
            f"🛡️ <b>You already have a valid subscription!</b>\n\n"
            f"Your access will expire on: <b>{expiry_str}</b>",
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
            set_user_subscription(message.from_user.id, expiry)
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

async def main():
    logging.info("Bot is running.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
