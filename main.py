import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"
WEBAPP_URL = os.environ.get("WEBAPP_URL") or "https://demo-qled.onrender.com/"

# Use an in-memory session so no api_id/api_hash required and no session file created
app = Client(":memory:", bot_token=BOT_TOKEN)

@app.on_message(filters.command("demo") & filters.private)
async def demo_handler(client, message):
    kb = InlineKeyboardMarkup(
        [[ InlineKeyboardButton("🚀 Open Music WebApp", web_app=WebAppInfo(url=WEBAPP_URL)) ]]
    )
    await message.reply_text("Click the button below to open the Music WebApp 👇", reply_markup=kb)

@app.on_message(filters.command("openweb"))
async def openweb_handler(client, message):
    kb = InlineKeyboardMarkup(
        [[ InlineKeyboardButton("🎵 Open WebApp", web_app=WebAppInfo(url=WEBAPP_URL)) ]]
    )
    await message.reply_text("Tap below:", reply_markup=kb)

if __name__ == "__main__":
    print("Pyrogram bot starting. Use /demo in a private chat with the bot.")
    app.run()
