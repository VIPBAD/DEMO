from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ⚠️ Important: apna bot token yahan set karo (ya environment variable se lo)
BOT_TOKEN = "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"

# WebApp URL (jo BotFather vich set kita hai)
WEBAPP_URL = "https://demo-qled.onrender.com/"

# /demo command
async def demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 Open Music WebApp", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
    await update.message.reply_text(
        "Click the button below to open the Music WebApp 👇",
        reply_markup=kb
    )

# Optional: still keep /openweb if you want
async def openweb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🎵 Open WebApp", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
    await update.message.reply_text("Tap below:", reply_markup=kb)

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("demo", demo))
    app.add_handler(CommandHandler("openweb", openweb))

    print("Bot running... use /demo in Telegram to test")
    app.run_polling()
