from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random

BOT_TOKEN = "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"

BOT_USERNAME = "ANONMUSIC11_BOT"
SHORTNAME    = "MiniMusic"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payload = update.effective_user.id  # or random/session id
    deeplink = f"https://t.me/{BOT_USERNAME}/{SHORTNAME}?startapp={payload}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎵 Open Music WebApp", url=deeplink)]])
    await update.message.reply_text("Tap the button to open the WebApp (tap, don't long-press).", reply_markup=kb)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
