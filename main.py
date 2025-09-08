from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random

BOT_TOKEN = "8410391376:AAF2GqNdUnl1Rh8CZIYwiwj3PfPv27-Dcg8"
BOT_USERNAME = "TGINLINEMUSICBOT"
SHORTNAME = "MiniMusic"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.message.chat
    payload = chat.id if chat.type in ['group', 'supergroup'] else user.id  # Use chat ID for groups, user ID otherwise
    deeplink = f"https://t.me/{BOT_USERNAME}/{SHORTNAME}?startapp={payload}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎵 Open Music WebApp", url=deeplink)]])
    await update.message.reply_text(
        f"Welcome, {user.first_name}! Tap the button to open the WebApp for {chat.title if chat.type in ['group', 'supergroup'] else 'your session'}.",
        reply_markup=kb
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
