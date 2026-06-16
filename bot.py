from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
import os
import time

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_state = {}

# ---------------- START ----------------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🤖 PRO File Bot Ready!\n\n"
        "📁 Send file to start."
    )

# ---------------- FILE INFO FUNCTION ----------------
def get_file_info(message: Message):
    file = message.document or message.video or message.audio

    size = file.file_size / (1024 * 1024)
    name = file.file_name if hasattr(file, "file_name") else "media file"

    return f"""
📄 File Info:

📌 Name: {name}
📦 Size: {size:.2f} MB
"""

# ---------------- FILE RECEIVER ----------------
@app.on_message(filters.document | filters.video | filters.audio)
def get_file(_, message: Message):

    user_id = message.from_user.id

    user_state[user_id] = {
        "file": message,
        "step": "choose"
    }

    info = get_file_info(message)

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Rename", callback_data="rename")],
        [InlineKeyboardButton("📊 Info", callback_data="info")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

    message.reply_text(info, reply_markup=buttons)

# ---------------- CALLBACK ----------------
@app.on_callback_query()
def callback(_, query: CallbackQuery):

    user_id = query.from_user.id
    query.answer()

    if user_id not in user_state:
        query.message.edit_text("❌ Session expired")
        return

    if query.data == "cancel":
        user_state.pop(user_id, None)
        query.message.edit_text("❌ Cancelled")
        return

    if query.data == "info":
        message = user_state[user_id]["file"]
        query.message.edit_text(get_file_info(message))
        return

    if query.data == "rename":
        user_state[user_id]["step"] = "rename"
        query.message.edit_text("✏ Send new file name:")
        return

# ---------------- PROGRESS SIMULATION ----------------
def fake_progress(text, percent):
    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
    return f"{text}\n\n[{bar}] {percent}%"

# ---------------- RENAME HANDLER ----------------
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message: Message):

    user_id = message.from_user.id

    if user_id not in user_state:
        return

    if user_state[user_id]["step"] != "rename":
        return

    try:
        new_name = message.text.strip()
        file_msg = user_state[user_id]["file"]

        msg = message.reply_text("⬇ Downloading... 0%")

        # DOWNLOAD WITH PROGRESS
        def progress(current, total):
            percent = int((current / total) * 100)
            try:
                msg.edit_text(fake_progress("⬇ Downloading...", percent))
            except:
                pass

        file_path = file_msg.download(progress=progress)

        msg.edit_text("✏ Renaming file...")

        ext = os.path.splitext(file_path)[1]
        new_file_path = f"{new_name}{ext}"

        os.rename(file_path, new_file_path)

        msg.edit_text("⬆ Uploading... 0%")

        # UPLOAD WITH PROGRESS
        def upload_progress(current, total):
            percent = int((current / total) * 100)
            try:
                msg.edit_text(fake_progress("⬆ Uploading...", percent))
            except:
                pass

        message.reply_document(
            document=new_file_path,
            caption="✅ Renamed Successfully!",
            progress=upload_progress
        )

        os.remove(new_file_path)
        user_state.pop(user_id, None)

    except Exception as e:
        message.reply_text(f"❌ Error: {e}")

app.run()
