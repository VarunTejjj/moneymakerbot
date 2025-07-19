import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Message, CallbackQuery
from aiogram.dispatcher.filters import Command

from config import BOT_TOKEN, PRIVATE_CHANNEL_LINK, UPI_ID
from screenshot_checker import check_screenshot
from subscription import generate_key

# Instantiate bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# /start command handler
@dp.message_handler(Command("start"))
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url="https://t.me/yourpublicchannel")],
        [InlineKeyboardButton(text="💰 Take Subscription", callback_data="subscribe")]
    ])
    await message.answer("👋 Welcome! Choose an option below:", reply_markup=keyboard)

# Callback for "Take Subscription"
@dp.callback_query_handler(lambda c: c.data == "subscribe")
async def subscribe_instruction(call: CallbackQuery):
    await call.message.answer(
        "To get 7 days premium access:\n\n"
        "💸 **Pay ₹5** to the UPI ID:\n"
        f"`{UPI_ID}`\n\n"
        "📸 Then send your payment screenshot here.",
        parse_mode=ParseMode.MARKDOWN
    )

# Handle screenshot image
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: Message):
    wait_msg = await message.reply("📸 Checking screenshot... please wait")

    # Save photo to file
    photo = message.photo[-1]
    file_path = f"screenshot_{message.from_user.id}.jpg"
    await photo.download(file_path)

    # Call checker
    is_valid, upi_matches = check_screenshot(file_path)

    if is_valid:
        key = generate_key()
        invite_link = await bot.create_chat_invite_link(
            chat_id=PRIVATE_CHANNEL_LINK,
            expire_date=int(asyncio.get_event_loop().time() + 600),
            member_limit=1
        )
        await message.answer(
            f"✅ *Payment Verified!*\n\n🔑 Your Key: `{key}`\n"
            f"📥 Access Channel: [Join Now]({invite_link.invite_link})\n\n"
            "⚠️ *This link is valid for 10 minutes and only usable once.*",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply("❌ UPI ID not found in the screenshot. Try again.")

    # Cleanup
    os.remove(file_path)
    await wait_msg.delete()

# Run the bot
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
