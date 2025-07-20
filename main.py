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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Join Channel", url="https://t.me/+nkPAaWA1TI8xOTVl")],
        [InlineKeyboardButton(text="💳 Get Subscription", callback_data="subscribe")]
    ])
    await message.answer_sticker('CAACAgUAAxkBAAED-d5lXlv4...')  # Replace with a real sticker ID for fun welcome
    await message.answer(
        "<b>Welcome to MoneyMaker Premium! 🚀</b>\n\n"
        "Unlock exclusive money-making tips and signals.\n\n"
        "1️⃣ <b>Pay</b> ₹5 to <code>{}</code>\n"
        "2️⃣ <b>Send your payment screenshot here.</b>\n"
        "3️⃣ <b>Get your key & one-time join link instantly!</b>".format(UPI_ID),
        parse_mode="HTML",
        reply_markup=keyboard
    )

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
        await call.message.answer_animation('https://media.giphy.com/media/XChk8P9qhzP3y/source.gif')  # Fun "payment" animation
        await call.message.answer(
            f"To get <b>7 days of premium access</b>:\n\n"
            f"💸 <b>Pay ₹5</b> to this UPI:\n"
            f"<code>{UPI_ID}</code>\n"
            f"Name: <b>{UPI_NAME}</b>\n\n"
            "Then send your payment screenshot here.",
            parse_mode="HTML"
        )

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: Message):
    await message.answer("🔎 Checking your payment screenshot, hold tight...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    image_data = await bot.download_file(file_path)
    tmp_path = f"{message.from_user.id}_screenshot.jpg"
    with open(tmp_path, "wb") as f:
        f.write(image_data.read())
    try:
        await asyncio.sleep(1.0)
        if check_screenshot(tmp_path):
            key = generate_key()
            now = int(time.time())
            expiry = now + KEY_VALIDITY_DAYS * 24 * 60 * 60
            set_user_subscription(message.from_user.id, expiry)

            # Generate the secure, one-time invite link
            invite = await bot.create_chat_invite_link(
                chat_id=-1002731631370,  # Your channel's ID
                member_limit=1,
                expire_date=now + 3600
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("📥 Join Private Channel", url=invite.invite_link)]
            ])
            await message.answer(
                f"✅ <b>Payment Verified!</b>\n\n"
                f"🔑 <b>Your Key:</b> <code>{key}</code>\n\n"
                "<i>Tap the button below to join the private channel.</i>\n"
                "⚠️ <b>This link is only for you and will expire in 1 hour.</b>",
                parse_mode="HTML",
                reply_markup=keyboard
            )

            async def delayed_revoke():
                await asyncio.sleep(600)
                try:
                    await bot.revoke_chat_invite_link(
                        chat_id=-1002731631370,
                        invite_link=invite.invite_link
                    )
                except Exception as e:
                    logging.warning(f"Failed to revoke invite: {e}")
            asyncio.create_task(delayed_revoke())
        else:
            await message.answer("❌ <b>Screenshot is invalid.</b>\nPlease send a valid UPI payment screenshot.", parse_mode="HTML")
    finally:
        os.remove(tmp_path)

async def main():
    logging.info("Bot started.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
