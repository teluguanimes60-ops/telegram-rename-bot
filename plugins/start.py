from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user

@Client.on_message(filters.command("start"))
def start(client, message):
    add_user(message.from_user.id)

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename_menu")],
        [InlineKeyboardButton("📊 Profile", callback_data="profile")]
    ])

    message.reply_text(
        "🤖 Full Utility Bot\n\nSelect option:",
        reply_markup=buttons
    )
