from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("start"))
def start(client, message):

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename File", callback_data="rename")],
        [InlineKeyboardButton("🎬 Video Tools", callback_data="video")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

    message.reply_text(
        "🔥 **AniToons Rename Bot**\n\nFull Utility Bot Ready 🚀",
        reply_markup=buttons
    )
