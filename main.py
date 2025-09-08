BOT_TOKEN = "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"  # apna Bot Token daalo

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
