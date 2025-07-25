# bot.py

import telebot
from telebot import types
from config import BOT_TOKEN, SOURCE_CHANNEL_ID, FORCE_JOIN_CHANNELS, ADMIN_ID, BOT_USERNAME
from utils import load_products, save_products, get_next_product_id
from blogger import create_post

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
products = load_products()
pending_links = {}  # Track admin posts awaiting affiliate link

# --- Simple HTTP server to satisfy Render's port detection ---

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT env var
    server = HTTPServer(("", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- Telegram bot handlers below ---

# Step 1: Detect product post in source channel
@bot.channel_post_handler(func=lambda msg: msg.chat.id == SOURCE_CHANNEL_ID)
def handle_new_product_post(msg):
    if msg.text or msg.caption or msg.photo:
        bot.send_message(
            ADMIN_ID,
            "Detected new product post.\nPlease reply with the original product (affiliate) link."
        )
        pending_links[ADMIN_ID] = msg

# Step 2: Receive original affiliate link from admin
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and ADMIN_ID in pending_links)
def receive_original_link(message):
    original_msg = pending_links.pop(ADMIN_ID)
    product_link = message.text.strip()

    # Extract product name and caption
    product_name = original_msg.caption.split("\n")[0] if original_msg.caption else "Product"
    caption_text = original_msg.caption if original_msg.caption else ""

    # Extract image URL if photo present
    image_url = ""
    if original_msg.photo:
        file_id = original_msg.photo[-1].file_id  # Get highest resolution photo
        file_info = bot.get_file(file_id)
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    # Generate next product ID
    next_pid = get_next_product_id(products)
    bot_start_link = f"https://t.me/{BOT_USERNAME}?start={next_pid}"

    try:
        # Create blogger post
        post_url = create_post(product_name, caption_text, image_url, bot_start_link)
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Error creating Blogger post:\n{e}")
        return

    # Save product info
    products[next_pid] = {
        "product_name": product_name,
        "image_url": image_url,
        "bot_start_link": bot_start_link,
        "blogger_post_url": post_url,
        "channel_message_id": original_msg.message_id,
        "caption": caption_text,
        "affiliate_link": product_link  # Storing the original affiliate link for buy button
    }
    save_products(products)

    # Delete original channel post
    try:
        bot.delete_message(SOURCE_CHANNEL_ID, original_msg.message_id)
    except Exception as e:
        print(f"Warning: Could not delete message: {e}")

    # Repost with new caption and inline button
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛍 View Product", url=post_url))

    repost_caption = (
        f"{caption_text}\n\n"
        f"🔗 <a href='{post_url}'>Product Blog</a>\n"
        f"🤖 <a href='{bot_start_link}'>View In Bot</a>"
    )

    if image_url:
        bot.send_photo(
            SOURCE_CHANNEL_ID,
            photo=image_url,
            caption=repost_caption,
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        bot.send_message(
            SOURCE_CHANNEL_ID,
            repost_caption,
            reply_markup=markup,
            parse_mode="HTML"
        )

# Step 3: Handle /start command with product ID
@bot.message_handler(commands=["start"])
def handle_start(message):
    args = message.text.split()
    if len(args) == 2:
        pid = args[1]
        user_id = message.from_user.id

        # Check if user joined all channels in FORCE_JOIN_CHANNELS
        not_joined = []
        for cid in FORCE_JOIN_CHANNELS:
            try:
                member = bot.get_chat_member(cid, user_id)
                if member.status not in ("member", "administrator", "creator"):
                    not_joined.append(cid)
            except Exception:
                not_joined.append(cid)

        if not_joined:
            markup = types.InlineKeyboardMarkup()
            for cid in not_joined:
                url = f"https://t.me/c/{str(cid)[4:]}"  # May fail if private channel
                markup.add(types.InlineKeyboardButton("Join Channel", url=url))
            markup.add(types.InlineKeyboardButton("✅ I've Joined", callback_data="check_joined"))
            bot.send_message(message.chat.id,
                             "Please join all required channels to access this product:",
                             reply_markup=markup)
            return

        product = products.get(pid)
        if product:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔗 Buy Now", url=product.get("affiliate_link", "#")))
            caption = f"<b>{product['product_name']}</b>\n\n{product.get('caption', '')}"
            bot.send_message(message.chat.id, caption, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Product not found or expired.")
    else:
        bot.send_message(message.chat.id, "Welcome! Use this bot after clicking a product link.")

# Step 4: Callback for "I've Joined" button
@bot.callback_query_handler(func=lambda call: call.data == "check_joined")
def check_joined_callback(call):
    user_id = call.from_user.id
    not_joined = []
    for cid in FORCE_JOIN_CHANNELS:
        try:
            member = bot.get_chat_member(cid, user_id)
            if member.status not in ("member", "administrator", "creator"):
                not_joined.append(cid)
        except Exception:
            not_joined.append(cid)

    if not not_joined:
        bot.send_message(call.message.chat.id, "Great! Now please /start the bot again with your product link.")
    else:
        bot.answer_callback_query(call.id, "Please join all channels first to continue.")

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
