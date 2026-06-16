from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from flask import Flask
import threading, os, re, time
from collections import deque

# -------- QUEUE --------
queue = deque()

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

# -------- STATES --------
user_files = {}
user_steps = {}

# -------- SMART RENAME --------
def smart_rename(filename):
    name, ext = os.path.splitext(filename)
    name = re.sub(r"(www\..*?\.)", "", name)
    name = re.sub(r"[_\-\.]+", " ", name)
    name = " ".join(name.split())
    return name + ext

# -------- START --------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🔥 **AniToon Pro Bot**\n\n"
        "📁 Send file to start\n"
        "⚡ Fast • Smart • Pro"
    )

# -------- FILE RECEIVE --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    user_id = message.from_user.id

    user_files[user_id] = message
    user_steps[user_id] = "waiting_button"

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨ Smart Rename", callback_data="smart"),
            InlineKeyboardButton("✏ Manual Rename", callback_data="manual")
        ],
        [
            InlineKeyboardButton("📊 File Info", callback_data="info")
        ]
    ])

    message.reply_text(
        "📁 File received!\nChoose option:",
        reply_markup=btn
    )

# -------- BUTTON HANDLER --------
@app.on_callback_query()
def cb(_, query):

    user_id = query.from_user.id

    if user_id not in user_files:
        query.answer("❌ Session expired", show_alert=True)
        return

    if query.data == "manual":
        user_steps[user_id] = "waiting_name"
        query.message.edit_text("✏ Send new file name")

    elif query.data == "smart":
        file_msg = user_files[user_id]

        file = file_msg.document or file_msg.video or file_msg.audio
        old_name = file.file_name if file.file_name else "file"

        new_name = smart_rename(old_name)

        query.message.edit_text(f"✨ Smart Name:\n\n`{new_name}`")

        process_file(query.message, file_msg, new_name, user_id)

    elif query.data == "info":
        user_steps[user_id] = "waiting_info"
        query.message.edit_text("📊 Send file again to get info")

# -------- TEXT RENAME --------
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "waiting_name":
        return

    if user_id not in user_files:
        return

    file_msg = user_files[user_id]
    new_name = message.text

    process_file(message, file_msg, new_name, user_id)

# -------- PROCESS FILE --------
def process_file(message, file_msg, new_name, user_id):

    start_time = time.time()
    progress_msg = message.reply_text("⏳ Starting...")

    # DOWNLOAD
    def progress(current, total):
        now = time.time()
        diff = now - start_time

        if diff == 0:
            return

        speed = current / diff
        percent = current * 100 / total
        remaining = (total - current) / speed if speed > 0 else 0

        progress_msg.edit_text(
            f"📥 **Downloading**\n\n"
            f"🔄 {percent:.1f}%\n"
            f"⚡ {speed/1024/1024:.2f} MB/s\n"
            f"⌛ {int(remaining)} sec left",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    file_path = file_msg.download(progress=progress)

    # RENAME
    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    upload_start = time.time()

    # UPLOAD
    def up_progress(current, total):
        now = time.time()
        diff = now - upload_start

        if diff == 0:
            return

        speed = current / diff
        percent = current * 100 / total
        remaining = (total - current) / speed if speed > 0 else 0

        progress_msg.edit_text(
            f"📤 **Uploading**\n\n"
            f"🚀 {percent:.1f}%\n"
            f"⚡ {speed/1024/1024:.2f} MB/s\n"
            f"⌛ {int(remaining)} sec left",
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

    user_files.pop(user_id, None)
    user_steps.pop(user_id, None)

# -------- INFO SYSTEM --------
@app.on_message(filters.document | filters.video | filters.audio)
def info_handler(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "waiting_info":
        return

    msg = message.reply_text("🔍 Analyzing...")

    file = message.document or message.video or message.audio

    name = file.file_name if file.file_name else "Unknown"
    size = round(file.file_size / (1024 * 1024), 2)

    text = (
        f"📊 **File Info**\n\n"
        f"📁 Name: `{name}`\n"
        f"📦 Size: {size} MB\n"
    )

    if message.video:
        text += f"⏱ Duration: {message.video.duration} sec\n"

    if message.audio:
        text += f"🎵 Duration: {message.audio.duration} sec\n"

    text += "\n⚠️ Languages & subtitles coming next..."

    msg.edit_text(text)

    user_steps.pop(user_id, None)

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app.run()
