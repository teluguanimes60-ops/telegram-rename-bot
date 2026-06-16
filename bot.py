from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from flask import Flask
import threading, os, re
from collections import deque

# -------- QUEUE --------
queue = deque()
is_processing = False

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

# -------- SMART RENAME --------
def smart_rename(filename):
    name = filename.replace(".", " ").replace("_", " ")

    junk = ["x264", "AAC", "HDRip", "BluRay", "WEBRip"]
    for j in junk:
        name = name.replace(j, "")

    ep = re.search(r'(?:Ep|Episode)?\s?(\d+)', name, re.IGNORECASE)
    quality = re.search(r'(\d{3,4}p)', name)

    title = name.strip()
    new_name = title

    if ep:
        new_name += f" - Episode {ep.group(1)}"

    if quality:
        new_name += f" [{quality.group(1)}]"

    return new_name

# -------- START --------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text("🔥 PRO Rename Bot\n\n📁 Send a file")

# -------- FILE RECEIVER (QUEUE) --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    queue.append(message)

    position = len(queue)

    message.reply_text(f"📥 Added to Queue!\n📍 Position: {position}")

    process_queue()

# -------- PROCESS QUEUE --------
def process_queue():
    global is_processing

    if is_processing or not queue:
        return

    is_processing = True

    while queue:
        message = queue.popleft()
        handle_file(message)

    is_processing = False

# -------- HANDLE FILE --------
def handle_file(message):

    user_id = message.from_user.id

    user_files[user_id] = message
    user_steps[user_id] = "waiting_name"

    # Suggest name
    original = message.document.file_name if message.document else "file"
    suggested = smart_rename(original)

    message.reply_text(
        f"✏ Send new file name\n\n💡 Suggested:\n`{suggested}`"
    )

# -------- RENAME --------
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "waiting_name":
        return

    if user_id not in user_files:
        return

    file_msg = user_files[user_id]
    original = file_msg.document.file_name if file_msg.document else "file"

    # AUTO SMART
    if message.text == ".":
        new_name = smart_rename(original)
    else:
        new_name = message.text

    progress_msg = message.reply_text("⏳ Starting...")

    # DOWNLOAD
    def progress(current, total):
        percent = int(current * 100 / total)
        progress_msg.edit_text(
            f"📥 Downloading...\n\n🔄 {percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    file_path = file_msg.download(progress=progress)

    # RENAME
    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    # UPLOAD
    def up_progress(current, total):
        percent = int(current * 100 / total)
        progress_msg.edit_text(
            f"📤 Uploading...\n\n🚀 {percent}%",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
            ])
        )

    message.reply_document(new_file, progress=up_progress)

    progress_msg.delete()

    os.remove(new_file)

    user_files.pop(user_id)
    user_steps.pop(user_id)

# -------- RUN --------
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app.run()
