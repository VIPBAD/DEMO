import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# --- Config ---
API_ID = int(os.environ.get("API_ID", 25742938))  # apna API ID daalo
API_HASH = os.environ.get("API_HASH", "b35b715fe8dc0a58e8048988286fc5b6")  # apna API Hash daalo
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI")  # apna Bot Token daalo

WEBAPP_URL = os.environ.get("WEBAPP_URL") or "https://demo-qled.onrender.com/"

# --- Bot Init ---
app = Client(
    "WebAppBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# /demo command (private only)
@app.on_message(filters.command("demo") & filters.private)
async def demo_handler(client, message):
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 Open Music WebApp", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
    await message.reply_text("Click below to open the WebApp 👇", reply_markup=kb)


# Run Bot
print("✅ Bot started...")
app.run()
