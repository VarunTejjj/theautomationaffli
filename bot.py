# bot.py

import telebot
from telebot import types
from config import BOT_TOKEN, SOURCE_CHANNEL_ID, FORCE_JOIN_CHANNELS, ADMIN_ID, BOT_USERNAME
from utils import load_products, save_products, get_next_product_id
from blogger import create_post

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
products = load_products()
pending_links = {}  # to handle admin link prompt flow

# Handler for new channel post
@bot.channel_post_handler(func=lambda msg: msg.chat.id == SOURCE_CHANNEL_ID)
def new_channel_post(msg):
    if msg.text or msg.caption or msg.photo:
        bot.send_message(
            ADMIN_ID,
            f"Detected new product post. Please send the original product (affiliate) link."
        )
        pending_links[ADMIN_ID] = msg

# Handler for admin's reply with affiliate link
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in pending_links)
def receive_affiliate_link(m):
    original_msg = pending_links.pop(ADMIN_ID)
    product_link = m.text.strip()
    # Extract info
    product_name = original_msg.caption.split("\n")[0] if original_msg.caption else "Product"
    caption = original_msg.caption if original_msg.caption else ""
    if original_msg.photo:
        file_id = original_msg.photo[-1].file_id
        image_info = bot.get_file(file_id)
        image_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{image_info.file_path}'
    else:
        image_url = ""
    # Product ID and links
    next_pid = get_next_product_id(products)
    bot_start_link = f"https://t.me/{BOT_USERNAME}?start={next_pid}"
    post_url = create_post(product_name, caption, image_url, bot_start_link)
    # Save to local DB
    products[next_pid] = {
        "product_name": product_name,
        "image_url": image_url,
        "bot_start_link": bot_start_link,
        "blogger_post_url": post_url,
        "channel_message_id": original_msg.message_id
    }
    save_products(products)
    # Delete original post
    bot.delete_message(SOURCE_CHANNEL_ID, original_msg.message_id)
    # Repost with new links and buttons
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛍 View Product", url=post_url))
    if image_url:
        bot.send_photo(
            SOURCE_CHANNEL_ID, image_url,
            caption=f"{caption}\n\n🔗 <a href='{post_url}'>Product Blog</a>\n🤖 <a href='{bot_start_link}'>View In Bot</a>",
            reply_markup=markup
        )
    else:
        bot.send_message(
            SOURCE_CHANNEL_ID,
            f"{caption}\n\n🔗 <a href='{post_url}'>Product Blog</a>\n🤖 <a href='{bot_start_link}'>View In Bot</a>",
            reply_markup=markup
        )

# Bot start command for users
@bot.message_handler(commands=["start"])
def handle_start(m):
    if len(m.text.split()) > 1:
        pid = m.text.split()[1]
        joined = all(
            bot.get_chat_member(cid, m.from_user.id).status in ["member", "administrator", "creator"]
            for cid in FORCE_JOIN_CHANNELS
        )
        if not joined:
            markup = types.InlineKeyboardMarkup()
            for cid in FORCE_JOIN_CHANNELS:
                markup.add(types.InlineKeyboardButton("Join Channel", url=f"https://t.me/c/{str(cid)[4:]}"))
            markup.add(types.InlineKeyboardButton("✅ I've Joined", callback_data="check_joined"))
            bot.send_message(m.chat.id, "Please join all required channels and click below.", reply_markup=markup)
            return
        product = products.get(pid)
        if product:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔗 Buy Now", url=product.get("blogger_post_url")))
            bot.send_message(
                m.chat.id,
                f"<b>{product['product_name']}</b>\n\n{product.get('caption', '')}",
                reply_markup=markup
            )
        else:
            bot.send_message(m.chat.id, "Product not found.")

@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
def recheck_joined(call):
    joined = all(
        bot.get_chat_member(cid, call.from_user.id).status in ["member", "administrator", "creator"]
        for cid in FORCE_JOIN_CHANNELS
    )
    if joined:
        bot.send_message(call.message.chat.id, "Thank you! Please /start the bot again with your product.")
    else:
        bot.answer_callback_query(call.id, "Please join all channels first.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
