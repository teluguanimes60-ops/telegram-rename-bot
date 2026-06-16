from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from flask import Flask
import threading, os, re, time

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
    return name

# -------- START --------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🔥 **AniToon Pro Bot**\n\nSend file to start"
    )

# -------- SINGLE FILE HANDLER (FIXED) --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    user_id = message.from_user.id

    # -------- INFO MODE --------
    if user_steps.get(user_id) == "waiting_info":

        msg = message.reply_text("🔍 Analyzing...")

        file = message.document or message.video or message.audio

        name = file.file_name if file.file_name else "Unknown"
        size = round(file.file_size / (1024 * 1024), 2)

        text = f"📊 **File Info**\n\n📁 {name}\n📦 {size} MB\n"

        if message.video:
            text += f"⏱ Duration: {message.video.duration} sec\n"

        if message.audio:
            text += f"🎵 Duration: {message.audio.duration} sec\n"

        msg.edit_text(text)

        user_steps.pop(user_id, None)
        return

    # -------- NORMAL FLOW --------
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

    message.reply_text("📁 File received!", reply_markup=btn)

# -------- BUTTON --------
@app.on_callback_query()
def cb(_, query):

    user_id = query.from_user.id

    if user_id not in user_files:
        query.answer("❌ Expired", show_alert=True)
        return

    file_msg = user_files[user_id]
    file = file_msg.document or file_msg.video or file_msg.audio

    if query.data == "manual":
        user_steps[user_id] = "waiting_name"
        query.message.edit_text("✏ Send new name")

    elif query.data == "smart":
        old_name = file.file_name if file.file_name else "file"
        new_name = smart_rename(old_name)

        query.message.edit_text(f"✨ Smart Name:\n`{new_name}`")

        process_file(query.message, file_msg, new_name, user_id)

    elif query.data == "info":
        user_steps[user_id] = "waiting_info"
        query.message.edit_text("📊 Send file again for info")

# -------- TEXT --------
@app.on_message(filters.text & ~filters.command("start"))
def rename(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "waiting_name":
        return

    file_msg = user_files[user_id]
    new_name = message.text

    process_file(message, file_msg, new_name, user_id)

# -------- PROCESS --------
def process_file(message, file_msg, new_name, user_id):

    start = time.time()
    msg = message.reply_text("⏳ Starting...")

    def progress(c, t):
        percent = int(c * 100 / t)
        msg.edit_text(f"📥 Downloading {percent}%")

    file_path = file_msg.download(progress=progress)

    ext = os.path.splitext(file_path)[1]
    new_file = new_name + ext
    os.rename(file_path, new_file)

    def up(c, t):
        percent = int(c * 100 / t)
        msg.edit_text(f"📤 Uploading {percent}%")

    message.reply_document(new_file, progress=up)

    msg.delete()
    os.remove(new_file)

    user_files.pop(user_id, None)
    user_steps.pop(user_id, None)

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app.run()
