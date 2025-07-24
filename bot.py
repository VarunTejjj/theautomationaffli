# bot.py

import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from google_auth import get_blogger_service
from config import (
    BOT_TOKEN,
    CHANNEL_1_ID,
    CHANNEL_2_ID,
    FORCE_JOIN_CHAT,
    ADSTERRA_SCRIPT,
    BLOGGER_BLOG_ID,
)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# State to hold the product message ID and wait for admin to enter original link
class PostState(StatesGroup):
    waiting_for_link = State()

# Store messages temporarily
post_data = {}

@dp.message_handler(content_types=types.ContentType.ANY, chat_type=types.ChatType.SUPERGROUP)
async def product_post_handler(message: types.Message):
    if message.chat.id != CHANNEL_1_ID:
        return

    admins = await bot.get_chat_administrators(message.chat.id)
    admin_ids = [admin.user.id for admin in admins]
    if message.from_user.id not in admin_ids:
        return

    # Save the product post content
    post_data[message.message_id] = message
    await message.reply("✅ Now send the original product link.", reply=False)
    await PostState.waiting_for_link.set()
    state = dp.current_state(user=message.from_user.id)
    await state.update_data(post_id=message.message_id)

@dp.message_handler(state=PostState.waiting_for_link, content_types=types.ContentType.TEXT)
async def handle_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")
    product_post = post_data.get(post_id)

    if not product_post:
        await message.reply("❌ Product post not found.")
        return

    product_link = message.text.strip()

    # Blogger API post
    service = get_blogger_service()
    content = f"{product_post.html_text}<br><br><a href='{product_link}'>🔗 Original Product</a><br><br>{ADSTERRA_SCRIPT}"

    post = service.posts().insert(
        blogId=BLOGGER_BLOG_ID,
        body={
            "title": "New Product Post",
            "content": content,
            "labels": ["Product", "Ad"],
        },
        isDraft=False
    ).execute()

    blogger_url = post.get("url")

    # Send post to Channel 2
    final_text = f"🆕 <b>New Product Added</b>\n\n{product_post.html_text}\n\n👉 <a href='{blogger_url}'>View Product</a>"
    await bot.send_message(CHANNEL_2_ID, final_text, disable_web_page_preview=False)

    await message.reply("✅ Successfully posted to Blogger & Channel 2!")
    await state.finish()

# Force join checker
@dp.message_handler(Command("start"))
async def start_cmd(message: types.Message):
    user = await bot.get_chat_member(FORCE_JOIN_CHAT, message.from_user.id)
    if user.status in ("left", "kicked"):
        btn = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/+yefc5k-8t1oxMDFl")
        )
        await message.answer("⚠️ Please join our channel to use this bot.", reply_markup=btn)
        return

    await message.answer("🤖 Bot is running. Only admins in Channel 1 can post.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
