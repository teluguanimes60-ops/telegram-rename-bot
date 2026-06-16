print("BOT STARTING...")
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from flask import Flask
import threading, os
from queue import Queue
import re

# -------- BOT --------
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------- FLASK (KEEP ALIVE) --------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot Running ✅"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# -------- DATA --------
task_queue = Queue()
user_files = {}
user_steps = {}

# -------- SMART RENAME --------
def smart_name(name):
    name = re.sub(r'\.', ' ', name)
    name = re.sub(r'[_\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title()

# -------- START --------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🔥 **AniToon's PRO Rename Bot**\n\n"
        "📁 Send any file to begin\n"
        "⚡ Fast | Smart | Clean UI"
    )

# -------- FILE RECEIVE --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    user_id = message.from_user.id

    user_files[user_id] = message
    user_steps[user_id] = "choose"

    # Smart suggestion
    file_name = message.document.file_name if message.document else "file"
    suggested = smart_name(os.path.splitext(file_name)[0])

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Auto Rename", callback_data="auto"),
            InlineKeyboardButton("✏ Manual Rename", callback_data="manual")
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]
    ])

    message.reply_text(
        f"📁 **File Received!**\n\n"
        f"💡 Suggested Name:\n`{suggested}`\n\n"
        f"Choose option 👇",
        reply_markup=btn
    )

# -------- BUTTON --------
@app.on_callback_query()
def buttons(_, query):

    user_id = query.from_user.id

    if query.data == "cancel":
        user_files.pop(user_id, None)
        user_steps.pop(user_id, None)
        query.message.edit_text("❌ Cancelled")
        return

    if user_id not in user_files:
        query.message.edit_text("❌ Session expired")
        return

    if query.data == "manual":
        user_steps[user_id] = "rename"
        query.message.edit_text("✏ Send new file name")

    elif query.data == "auto":
        file_msg = user_files[user_id]

        file_name = file_msg.document.file_name if file_msg.document else "file"
        new_name = smart_name(os.path.splitext(file_name)[0])

        process_file(file_msg, new_name, query.message)

# -------- TEXT RENAME --------
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "rename":
        return

    file_msg = user_files.get(user_id)
    if not file_msg:
        return

    new_name = message.text

    process_file(file_msg, new_name, message)

# -------- PROCESS FUNCTION --------
def process_file(file_msg, new_name, msg):

    user_id = file_msg.from_user.id

    progress_msg = msg.reply_text("⏳ Starting...")

    # -------- DOWNLOAD --------
    def progress(current, total):
        percent = int(current * 100 / total)

        progress_msg.edit_text(
            f"📥 **Downloading...**\n\n"
            f"🚀 {percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    file_path = file_msg.download(progress=progress)

    # -------- RENAME --------
    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    # -------- UPLOAD --------
    def up_progress(current, total):
        percent = int(current * 100 / total)

        progress_msg.edit_text(
            f"📤 **Uploading...**\n\n"
            f"⚡ {percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    file_msg.reply_document(
        document=new_file,
        caption="✅ **Done Successfully!**",
        progress=up_progress
    )

    progress_msg.delete()

    os.remove(new_file)

    user_files.pop(user_id, None)
    user_steps.pop(user_id, None)

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    print("BOT RUNNING...")
import time
from pyrogram.errors import FloodWait

while True:
    try:
        print("🚀 Starting bot...")
        app.run()
    except FloodWait as e:
        print(f"⚠️ FloodWait: sleeping {e.value} seconds")
        time.sleep(e.value)
