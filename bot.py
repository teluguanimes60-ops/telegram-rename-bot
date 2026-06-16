from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from flask import Flask
import threading, os
from queue import Queue

# -------- QUEUE SYSTEM --------
task_queue = Queue()

# -------- FLASK --------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot Running ✅"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# -------- BOT --------
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------- USER STATES --------
user_files = {}
user_steps = {}

# -------- START --------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🔥 PRO Rename Bot\n\n📁 Send a file to start"
    )

# -------- RECEIVE FILE --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    user_id = message.from_user.id

    user_files[user_id] = message
    user_steps[user_id] = "waiting_button"

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Rename", callback_data="rename")]
    ])

    message.reply_text(
        "📁 File received!\nChoose option:",
        reply_markup=btn
    )

# -------- BUTTON --------
@app.on_callback_query()
def cb(_, query):

    user_id = query.from_user.id

    if query.data == "rename":
        user_steps[user_id] = "waiting_name"
        query.message.edit_text("✏ Send new file name")

# -------- RENAME FLOW --------
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "waiting_name":
        return

    if user_id not in user_files:
        return

    file_msg = user_files[user_id]
    new_name = message.text

    # -------- PROGRESS UI --------
    progress_msg = message.reply_text("⏳ Starting...")

    def progress(current, total):
        percent = int(current * 100 / total)

        progress_msg.edit_text(
            f"📥 Downloading...\n\n🔄 {percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    # -------- DOWNLOAD --------
    file_path = file_msg.download(progress=progress)

    # -------- RENAME --------
    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    # -------- UPLOAD --------
    def up_progress(current, total):
        percent = int(current * 100 / total)

        progress_msg.edit_text(
            f"📤 Uploading...\n\n🚀 {percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    message.reply_document(
        new_file,
        caption="✅ Done!",
        progress=up_progress
    )

    progress_msg.delete()

    os.remove(new_file)
    user_files.pop(user_id)
    user_steps.pop(user_id)

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app.run()
