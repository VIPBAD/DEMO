from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import CommandHandler, Application, ContextTypes

BOT_TOKEN = "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"  # BotFather se naya token lo

WEBAPP_URL = "https://demo-qled.onrender.com"   # aapka FastAPI app
DEEPLINK   = "https://t.me/ANONMUSIC11_BOT/MiniMusic"  # BotFather me banaya link

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Open Music WebApp (in-app)", web_app=WebAppInfo(WEBAPP_URL))],
        [InlineKeyboardButton("🔗 Open via deep link", url=DEEPLINK)]
    ])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Tap the button below to open the Music WebApp:\n\n👉 Note: Tap (don’t long-press).",
        reply_markup=kb
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
