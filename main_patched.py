import asyncio
import os
import time
import datetime
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Message, CallbackQuery
from aiogram.dispatcher.filters import Command
from pymongo import MongoClient

from config import BOT_TOKEN, UPI_ID, UPI_NAME, KEY_VALIDITY_DAYS
from screenshot_checker import check_screenshot
from subscription import generate_key

# Enable basic logging
logging.basicConfig(level=logging.INFO)

# --- MongoDB Atlas connection (standard URI for Termux and servers) ---
MONGODB_URI = "mongodb://thepvt:MadMax31@thepvt-shard-00-00.1pyehh7.mongodb.net:27017,thepvt-shard-00-01.1pyehh7.mongodb.net:27017,thepvt-shard-00-02.1pyehh7.mongodb.net:27017/?ssl=true&replicaSet=atlas-mqak2q-shard-0&authSource=admin&retryWrites=true&w=majority"
client = MongoClient(MONGODB_URI)
db = client["moneymaker"]
subs = db["subscriptions"]

def get_user_expiry(user_id):
    doc = subs.find_one({"user_id": user_id, "expiry": {"$gt": int(time.time())}})
    return doc["expiry"] if doc else 0

def set_user_subscription(user_id, key, expiry):
    subs.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "key": key, "expiry": expiry}},
        upsert=True
    )

def store_key(key, expiry, user_id):
    subs.insert_one({"key": key, "expiry": expiry, "user_id": user_id})

# --- aiogram setup ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(Command("start"))
async def start(message: Message):
    logging.info(f"/start used by {message.from_user.id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ðŸ“¢ Join Channel", url="https://t.me/yourpublicchannel")],
        [InlineKeyboardButton(text="ðŸ’° Take Subscription", callback_data="subscribe")]
    ])
    await message.answer("Welcome! Choose an option below:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "subscribe")
async def subscribe_instruction(call: CallbackQuery):
    print("ðŸ’° 'Take Subscription' button clicked by:", call.from_user.id)
    try:
        await call.answer()

        await call.answer()
    except Exception as e:
        logging.warning(f"Failed to answer callback: {e}")
    user_id = call.from_user.id
    now = int(time.time())
    expiry = get_user_expiry(user_id)
    logging.info(f"Subscribe pressed by {user_id}, expiry: {expiry}")
    if expiry > now:
        expiry_str = datetime.datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        await call.message.answer(
            f"ðŸ›¡ï¸ You already have a valid subscription!\n\n"
            f"Your access will expire on: <b>{expiry_str}</b>",
            parse_mode="HTML"
        )
    else:
        await call.message.answer(
            "To get 7 days premium access:\n\n"
            f"**Pay â‚¹5** to the UPI ID:\n"
            f"`{UPI_ID}`\n"
            f"Name: *{UPI_NAME}*\n\n"
            "Then send your payment screenshot here.",
            parse_mode=ParseMode.MARKDOWN
        )

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: Message):
    logging.info(f"Photo received from {message.from_user.id}")
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
            store_key(key, expiry, message.from_user.id)
            invite = await bot.create_chat_invite_link(
                chat_id=-1002731631370,
                member_limit=1,
                expire_date=now + 3600
            )
            await message.answer(
                f"âœ… Payment Verified!\n\n"
                f"ðŸ”‘ Your Key: `{key}`\n"
                f"ðŸ“¥ [Tap here to join the private channel]({invite.invite_link})\n"
                f"âš ï¸ This link can only be used once and will expire in 1 hour.",
                parse_mode=ParseMode.MARKDOWN
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
            await message.answer("âŒ Screenshot is invalid. Please send a valid UPI payment screenshot.")
    except Exception as e:
        logging.error(f"Error in handle_photo: {e}")
        await message.answer("An error occurred while checking your screenshot. Please try again.")
    finally:
        os.remove(tmp_path)

async def main():
    logging.info("Bot started.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
