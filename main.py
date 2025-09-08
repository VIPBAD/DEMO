from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, Application, ContextTypes

BOT_TOKEN = "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"

DEEPLINK = "https://t.me/ANONMUSIC11_BOT/MiniMusic"  # BotFather ka WebApp link

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Open Music WebApp", url=DEEPLINK)]
    ])

    await update.message.reply_text(
        "Tap below to open the Music WebApp:\n\n👉 Note: Tap (don’t long-press).",
        reply_markup=kb
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
