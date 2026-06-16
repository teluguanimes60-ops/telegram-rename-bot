from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
import os, re, time, threading
from queue import Queue
from pyrogram.errors import FloodWait

# -------- BOT --------
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

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
        "🔥 PRO Rename Bot\n\n📁 Send file to start"
    )

# -------- RECEIVE FILE --------
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, message):

    user_id = message.from_user.id

    user_files[user_id] = message
    user_steps[user_id] = "choose"

    file_name = message.document.file_name if message.document else "file"
    suggested = smart_name(os.path.splitext(file_name)[0])

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Auto", callback_data="auto"),
            InlineKeyboardButton("✏ Manual", callback_data="manual")
        ]
    ])

    message.reply_text(
        f"📁 File Received!\n\n💡 Suggested:\n`{suggested}`",
        reply_markup=btn
    )

# -------- BUTTON --------
@app.on_callback_query()
def buttons(_, query):

    user_id = query.from_user.id

    if user_id not in user_files:
        try:
            query.message.edit_text("❌ Session expired")
        except:
            pass
        return

    if query.data == "manual":
        user_steps[user_id] = "rename"
        query.message.edit_text("✏ Send new name")

    elif query.data == "auto":
        file_msg = user_files[user_id]

        file_name = file_msg.document.file_name if file_msg.document else "file"
        new_name = smart_name(os.path.splitext(file_name)[0])

        task_queue.put((file_msg, new_name, query.message))
        query.message.edit_text("⏳ Added to queue...")

# -------- TEXT --------
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "rename":
        return

    file_msg = user_files.get(user_id)
    if not file_msg:
        return

    new_name = message.text

    task_queue.put((file_msg, new_name, message))
    message.reply_text("⏳ Added to queue...")

# -------- WORKER --------
def worker():
    while True:
        file_msg, new_name, msg = task_queue.get()

        try:
            process_file(file_msg, new_name, msg)
        except Exception as e:
            msg.reply_text(f"❌ Error: {e}")

        task_queue.task_done()

# -------- PROCESS --------
def process_file(file_msg, new_name, msg):

    user_id = file_msg.from_user.id

    progress_msg = msg.reply_text("⏳ Starting...")

    last_percent = {"down": -1, "up": -1}

    # -------- DOWNLOAD --------
    def progress(current, total):
        percent = int(current * 100 / total)

        if percent == last_percent["down"]:
            return

        last_percent["down"] = percent

        try:
            progress_msg.edit_text(
                f"📥 Downloading...\n\n🔄 {percent}%",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
                ])
            )
        except:
            pass

    file_path = file_msg.download(progress=progress)

    # -------- RENAME --------
    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    # -------- UPLOAD --------
    def up_progress(current, total):
        percent = int(current * 100 / total)

        if percent == last_percent["up"]:
            return

        last_percent["up"] = percent

        try:
            progress_msg.edit_text(
                f"📤 Uploading...\n\n🚀 {percent}%",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔔 Join Channel", url="https://t.me/Anitoon_edit/33")]
                ])
            )
        except:
            pass

    file_msg.reply_document(
        new_file,
        caption=f"✅ Renamed: {new_name}",
        progress=up_progress
    )

    try:
        progress_msg.delete()
    except:
        pass

    os.remove(new_file)

    user_files.pop(user_id, None)
    user_steps.pop(user_id, None)

# -------- RUN --------
if __name__ == "__main__":

    threading.Thread(target=worker, daemon=True).start()

    while True:
        try:
            print("🚀 Bot Starting...")
            app.run()
        except FloodWait as e:
            print(f"FloodWait: {e.value}")
            time.sleep(e.value)
