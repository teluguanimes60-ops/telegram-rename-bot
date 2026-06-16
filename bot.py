from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from flask import Flask
import threading, os
from queue import Queue

# -------- QUEUE --------
task_queue = Queue()

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

# -------- START --------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🔥 PRO Rename Bot\n\n📁 Send a file"
    )

# -------- FILE HANDLER --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    task_queue.put(message)

    message.reply_text(
        f"📥 Added to queue\n⏳ Position: {task_queue.qsize()}"
    )

# -------- PROCESS --------
def process_file(message):

    user_id = message.from_user.id

    # ask name
    ask = message.reply_text("✏ Send new file name")
    new_msg = app.listen(user_id)
    new_name = new_msg.text

    progress_msg = message.reply_text("⏳ Starting...")

    # download
    def progress(current, total):
        percent = int(current * 100 / total)
        progress_msg.edit_text(
            f"📥 Downloading...\n\n{percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    file_path = message.download(progress=progress)

    # rename
    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    # upload
    def up_progress(current, total):
        percent = int(current * 100 / total)
        progress_msg.edit_text(
            f"📤 Uploading...\n\n{percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    message.reply_document(new_file, progress=up_progress)

    progress_msg.delete()
    os.remove(new_file)

# -------- WORKER --------
def worker():
    while True:
        msg = task_queue.get()

        try:
            process_file(msg)
        except Exception as e:
            msg.reply_text(f"❌ Error: {e}")

        task_queue.task_done()

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=run_web).start()
    app.run()
