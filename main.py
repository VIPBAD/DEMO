# --- Config ---
API_ID = int(os.environ.get("API_ID", 25742938))  # apna API ID daalo
API_HASH = os.environ.get("API_HASH", "b35b715fe8dc0a58e8048988286fc5b6")  # apna API Hash daalo
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI")  # apna Bot Token daalo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CommandHandler, Application
import os

async def start(update, context):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎵 Open Music WebApp",
                    web_app=WebAppInfo("https://demo-qled.onrender.com")
                )
            ]
        ]
    )
    await update.message.reply_text("Click below to open:", reply_markup=kb)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
