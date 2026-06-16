from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

user_state = {}

@Client.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, message):

    user_id = message.from_user.id

    user_state[user_id] = {
        "file": message,
        "step": "choose"
    }

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Rename", callback_data="rename")],
        [InlineKeyboardButton("📊 Info", callback_data="info")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

    message.reply_text("📁 File received", reply_markup=buttons)

@Client.on_callback_query()
def callbacks(client, query):

    user_id = query.from_user.id
    query.answer()

    if query.data == "cancel":
        user_state.pop(user_id, None)
        query.message.edit_text("❌ Cancelled")

    elif query.data == "rename":
        user_state[user_id]["step"] = "rename"
        query.message.edit_text("✏ Send new name")

    elif query.data == "info":
        file = user_state[user_id]["file"]
        size = file.document.file_size / (1024*1024)
        query.message.edit_text(f"📦 Size: {size:.2f} MB")

@Client.on_message(filters.text)
def rename_process(client, message):

    user_id = message.from_user.id

    if user_id not in user_state:
        return

    if user_state[user_id]["step"] != "rename":
        return

    new_name = message.text
    file_msg = user_state[user_id]["file"]

    path = file_msg.download()

    ext = os.path.splitext(path)[1]
    new_path = f"{new_name}{ext}"

    os.rename(path, new_path)

    message.reply_document(new_path, caption="✅ Done")

    os.remove(new_path)
    user_state.pop(user_id)
