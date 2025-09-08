from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8410391376:AAF2GqNdUnl1Rh8CZIYwiwj3PfPv27-Dcg8"
BOT_USERNAME = "TGINLINEMUSICBOT"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # WebApp URL with startapp=chat.id (for group context)
    url = f"https://demo-qled.onrender.com/?startapp={chat.id}"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Open Music WebApp", web_app=WebAppInfo(url=url))]
    ])

    await update.message.reply_text(
        f"Welcome {user.first_name}! Tap the button to open the WebApp for "
        f"{chat.title if chat.type in ['group', 'supergroup'] else 'your session'}.",
        reply_markup=kb
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
