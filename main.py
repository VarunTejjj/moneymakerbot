# main.py
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN, PRIVATE_CHANNEL_LINK
from screenshot_checker import check_screenshot
from subscription import generate_key

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url="https://t.me/yourpublicchannel")],
        [InlineKeyboardButton(text="💰 Take Subscription", callback_data="subscribe")]
    ])
    await message.answer("Welcome! Choose an option below:", reply_markup=keyboard)

@dp.callback_query(lambda call: call.data == "subscribe")
async def subscribe_instruction(call: CallbackQuery):
    await call.message.answer(
        "To get 7 days premium access:\n\n"
        "**Pay ₹5** to the UPI ID:\n"
        "`kothapellivaruntej31@fam`\n"
        "Name: *Kotha Pally Sanjana*\n\n"
        "Then send your payment screenshot here.",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message()
async def handle_photo(message: Message):
    if not message.photo:
        return

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    downloaded = await bot.download_file(file_path)

    image_path = f"{message.from_user.id}_screenshot.jpg"
    with open(image_path, "wb") as f:
        f.write(downloaded.read())

    if check_screenshot(image_path):
        key = generate_key()
        await message.answer(
            f"✅ Payment Verified!\n\n"
            f"🔑 Your Key: `{key}`\n"
            f"📥 Access Private Channel: {PRIVATE_CHANNEL_LINK}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer("❌ Screenshot is invalid. Please send a valid UPI payment screenshot.")

    os.remove(image_path)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
