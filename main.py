from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = "8410391376:AAF2GqNdUnl1Rh8CZIYwiwj3PfPv27-Dcg8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://demo-qled.onrender.com/"  # aapki deployed MiniApp URL
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Open Music WebApp", web_app=WebAppInfo(url=url))]
    ])
    chat = update.effective_chat
    await update.message.reply_text(
        f"Welcome to WebApp in {chat.title if chat.type != 'private' else 'your chat'}!",
        reply_markup=kb
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
