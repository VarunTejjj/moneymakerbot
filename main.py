import asyncio
import os
import time
import datetime
import logging
import json

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Message, CallbackQuery
from aiogram.dispatcher.filters import Command

from config import BOT_TOKEN, UPI_ID, UPI_NAME, KEY_VALIDITY_DAYS
from screenshot_checker import check_screenshot
from subscription import generate_key

# File to store subscriptions: {user_id: expiry}
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

# --- aiogram setup ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(Command("start"))
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url="https://t.me/yourpublicchannel")],
        [InlineKeyboardButton(text="💰 Take Subscription", callback_data="subscribe")]
    ])
    await message.answer("Welcome! Choose an option below:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "subscribe")
async def subscribe_instruction(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    now = int(time.time())
    expiry = get_user_expiry(user_id)
    if expiry > now:
        expiry_str = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        await call.message.answer(
            f"🛡️ You already have a valid subscription!\n\n"
            f"Your access will expire on: <b>{expiry_str}</b>",
            parse_mode="HTML"
        )
    else:
        await call.message.answer(
            "To get 7 days premium access:\n\n"
            f"**Pay ₹5** to the UPI ID:\n"
            f"`{UPI_ID}`\n"
            f"Name: *{UPI_NAME}*\n\n"
            "Then send your payment screenshot here.",
            parse_mode=ParseMode.MARKDOWN
        )

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: Message):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    image_data = await bot.download_file(file_path)
    tmp_path = f"{message.from_user.id}_screenshot.jpg"
    with open(tmp_path, "wb") as f:
        f.write(image_data.read())

    if check_screenshot(tmp_path):
        key = generate_key()
        now = int(time.time())
        expiry = now + KEY_VALIDITY_DAYS * 24 * 60 * 60
        set_user_subscription(message.from_user.id, expiry)
        await message.answer(
            f"✅ Payment Verified!\n\n"
            f"🔑 Your Key: `{key}`\n"
            f"📥 [Tap here to join the private channel](https://t.me/+nkPAaWA1TI8xOTVl)\n"
            f"⚠️ Keep your code safe for website use. This key gives you full access for 7 days.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer("❌ Screenshot is invalid. Please send a valid UPI payment screenshot.")

    os.remove(tmp_path)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
