# send_webapp_button.py  (python-telegram-bot v20+)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"

async def openweb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://demo-qled.onrender.com/"   # your web app URL
    kb = InlineKeyboardMarkup(
        [[ InlineKeyboardButton("Open Music WebApp", web_app=WebAppInfo(url=url)) ]]
    )
    await update.message.reply_text("Open web app:", reply_markup=kb)

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("openweb", openweb))
    app.run_polling()
