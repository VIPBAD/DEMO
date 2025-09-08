# pyro_webapp_bot.py
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Get token from env for safety (recommended)
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"
# Replace above hardcoded token with env var in production.

# Your webapp URL (set this in BotFather as well)
WEBAPP_URL = os.environ.get("WEBAPP_URL") or "https://demo-qled.onrender.com/"

# Create Pyrogram Client for bot
app = Client("musicbot", bot_token=BOT_TOKEN)


# /demo command handler
@app.on_message(filters.command("demo") & filters.private)
async def demo_handler(client, message):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🚀 Open Music WebApp",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ]
    )
    await message.reply_text("Click the button below to open the Music WebApp 👇", reply_markup=kb)


# optional /openweb (works in groups and private)
@app.on_message(filters.command("openweb"))
async def openweb_handler(client, message):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎵 Open WebApp",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ]
    )
    await message.reply_text("Tap below:", reply_markup=kb)


if __name__ == "__main__":
    print("Pyrogram bot starting. Use /demo in a private chat with the bot.")
    app.run()
