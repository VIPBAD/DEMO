# REPLACE BOT_TOKEN with your new token (do NOT paste token publicly)
BOT_TOKEN = "8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI"

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CommandHandler, Application, ContextTypes
from telegram import Update

# Short deep link (replace with your real bot username/shortname)
DEEP_LINK = "https://t.me/ANONMUSIC11_BOT/MiniMusic"
WEBAPP_URL = "https://demo-qled.onrender.com"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /start — replies with both a web_app button and a deep-link button.
    Works in private chats and groups (bot must be present in the group).
    """
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Open Music WebApp (in-app)", web_app=WebAppInfo(WEBAPP_URL))
        ],
        [
            InlineKeyboardButton("🔗 Open / Share (deep link)", url=DEEP_LINK)
        ]
    ])
    await update.message.reply_text(
        "Tap below to open the Music WebApp (tap, don't long-press):",
        reply_markup=kb
    )

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Use /share in any chat (group or private) to post the same webapp + deep-link keyboard.
    Useful to broadcast or place it in a group chat.
    """
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Open Music WebApp (in-app)", web_app=WebAppInfo(WEBAPP_URL))
        ],
        [
            InlineKeyboardButton("🔗 Open / Share (deep link)", url=DEEP_LINK)
        ]
    ])
    # update.effective_chat is the chat where the command was sent (works in groups)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Open the Music WebApp (tap, don't long-press):",
                                   reply_markup=kb)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("share", share))  # use /share to post in group
    app.run_polling()

if __name__ == "__main__":
    main()
