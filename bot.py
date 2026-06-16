from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from flask import Flask
import threading, os, time

# -------- FLASK --------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# -------- BOT --------
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_files = {}

# -------- START --------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🔥 PRO Rename Bot\n\nSend a file to begin."
    )

# -------- RECEIVE FILE --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    user_files[message.from_user.id] = message

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Rename", callback_data="rename")]
    ])

    message.reply_text("📁 File received", reply_markup=btn)

# -------- BUTTON --------
@app.on_callback_query()
def cb(_, query):

    if query.data == "rename":
        query.message.edit_text("✏ Send new name")

# -------- RENAME --------
@app.on_message(filters.text & ~filters.command("start"))
def rename(_, message):

    user_id = message.from_user.id

    if user_id not in user_files:
        return

    file_msg = user_files[user_id]
    new_name = message.text

    # Progress message
    progress_msg = message.reply_text("⏳ Processing... 0%")

    # Download
    def progress(current, total):
        percent = int(current * 100 / total)
        progress_msg.edit_text(
            f"📥 Downloading...\n\n{percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    file_path = file_msg.download(progress=progress)

    # Rename
    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    # Upload progress
    def up_progress(current, total):
        percent = int(current * 100 / total)
        progress_msg.edit_text(
            f"📤 Uploading...\n\n{percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    message.reply_document(
        new_file,
        progress=up_progress
    )

    progress_msg.delete()

    os.remove(new_file)
    user_files.pop(user_id)

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app.run()
