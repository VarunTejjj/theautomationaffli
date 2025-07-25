# bot.py

import telebot
from telebot import types
from config import BOT_TOKEN, SOURCE_CHANNEL_ID, FORCE_JOIN_CHANNELS, ADMIN_ID, BOT_USERNAME
from utils import load_products, save_products, get_next_product_id
from blogger import create_post

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
products = load_products()
pending_links = {}  # Admin message awaiting affiliate link

# Simple HTTP server for Render port detection
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()


# Step 1: Detect new product post in the channel
@bot.channel_post_handler(content_types=['text', 'photo'])
def on_new_channel_post(msg):
    if msg.text or msg.caption or msg.photo:
        bot.send_message(
            ADMIN_ID,
            "New product post detected.\nPlease reply here with the original product affiliate link."
        )
        pending_links[ADMIN_ID] = msg

# Step 2: Receive affiliate link from admin and process product
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in pending_links)
def on_receive_affiliate_link(message):
    original_msg = pending_links.pop(ADMIN_ID)
    affiliate_link = message.text.strip()

    product_name = original_msg.caption.split("\n")[0] if original_msg.caption else "Product"
    caption_text = original_msg.caption if original_msg.caption else ""

    product_id = get_next_product_id(products)
    bot_start_link = f"https://t.me/{BOT_USERNAME}?start={product_id}"

    try:
        post_url = create_post(product_name, caption_text, "", bot_start_link)
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Failed to create Blogger post:\n{e}")
        return

    # Prepare the Inline Keyboard markup
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛍 View Product", url=post_url))

    repost_caption = caption_text if caption_text else ""

    image_url = ""
    photo_file = None
    if original_msg.photo:
        file_id = original_msg.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        from io import BytesIO
        photo_file = BytesIO(downloaded_file)
        photo_file.name = "image.jpg"  # Telegram expects file-like object to have name attribute

        image_url = None  # Since we'll upload file directly, no need for image_url here
    else:
        photo_file = None

    # Save the product info with image_url key as empty string or None (since photo_file is used)
    products[product_id] = {
        "product_name": product_name,
        "image_url": "",  # or None, because we upload directly
        "bot_start_link": bot_start_link,
        "blogger_post_url": post_url,
        "channel_message_id": original_msg.message_id,
        "caption": caption_text,
        "affiliate_link": affiliate_link
    }
    save_products(products)

    try:
        bot.delete_message(SOURCE_CHANNEL_ID, original_msg.message_id)
    except Exception:
        pass  # May fail if insufficient rights or message already deleted

    if photo_file:
        try:
            photo_file.seek(0)
            bot.send_photo(
                SOURCE_CHANNEL_ID,
                photo=photo_file,
                caption=repost_caption,
                reply_markup=markup,
                parse_mode="HTML" if repost_caption else None
            )
        except Exception as e:
            bot.send_message(ADMIN_ID, f"Failed to repost image: {e}")
    else:
        bot.send_message(
            SOURCE_CHANNEL_ID,
            repost_caption or "Product",
            reply_markup=markup,
            parse_mode="HTML" if repost_caption else None
        )

# Step 3: Handle /start command for all users, enforce force join
@bot.message_handler(commands=["start"])
def on_start_command(message):
    user_id = message.from_user.id

    # Always check force-join channels on every /start
    not_joined = []
    for channel in FORCE_JOIN_CHANNELS:
        cid = channel["id"]
        try:
            member_status = bot.get_chat_member(cid, user_id).status
            if member_status not in ("member", "administrator", "creator"):
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)

    if not_joined:
        markup = types.InlineKeyboardMarkup()
        for channel in not_joined:
            markup.add(types.InlineKeyboardButton("Join Channel", url=channel["invite_link"]))
        markup.add(types.InlineKeyboardButton("✅ I've Joined", callback_data="check_joined"))
        bot.send_message(
            message.chat.id,
            "Please join the required channels first to use this bot.",
            reply_markup=markup
        )
        return

    args = message.text.split()
    if len(args) == 2:
        product_id = args[1]
        product = products.get(product_id)
        if product:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔗 Buy Now", url=product.get("affiliate_link", "#")))
            bot.send_message(
                message.chat.id,
                f"<b>{product['product_name']}</b>\n\n{product.get('caption', '')}",
                reply_markup=markup,
                parse_mode="HTML"
            )
        else:
            bot.send_message(message.chat.id, "Sorry, product not found.")
    else:
        bot.send_message(message.chat.id, "Welcome! Send me a product link to get started.")


# Step 4: Callback query handler for join confirmation button
@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
def on_check_joined(call):
    user_id = call.from_user.id
    not_joined_channels = []
    for channel in FORCE_JOIN_CHANNELS:
        cid = channel["id"]
        try:
            member_status = bot.get_chat_member(cid, user_id).status
            if member_status not in ("member", "administrator", "creator"):
                not_joined_channels.append(channel)
        except Exception:
            not_joined_channels.append(channel)

    if not not_joined_channels:
        bot.send_message(call.message.chat.id, "Thanks for joining! Please /start the bot again with your product link.")
    else:
        bot.answer_callback_query(call.id, "Please join all required channels first.")


if __name__ == "__main__":
    print("Bot started...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot polling stopped due to error: {e}")
        sys.exit(1)
