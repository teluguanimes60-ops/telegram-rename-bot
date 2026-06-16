from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserNotParticipant
from config import *
import os, re, time, threading
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
CHANNEL = "Anitoon_edit"
CHANNEL_POST = "https://t.me/Anitoon_edit/33"

# ===== FLASK =====
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot Running ✅"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# ===== BOT =====
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_steps = {}

# ===== JOIN CHECK =====
def is_joined(client, user_id):
    try:
        client.get_chat_member(CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except:
        return True

# ===== SMART RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+|www\.\S+', '', name)
    name = re.sub(r'\b(480p|720p|1080p|4k|HDRip|WEBRip|BluRay|x264|x265)\b', '', name, flags=re.I)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title() or "AniToon_File"

# ===== UI =====
def progress_bar(p):
    return "█" * int(p/10) + "░" * (10-int(p/10))

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 AniToon's Channel List", url=CHANNEL_POST)]
    ])

def safe_edit(msg, text, btn=None):
    try:
        msg.edit_text(text, reply_markup=btn)
    except:
        pass

# ===== MAIN MENU =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="menu_rename")],
        [InlineKeyboardButton("🎬 Video Tools", callback_data="menu_video")],
        [InlineKeyboardButton("⚙ Settings", callback_data="menu_settings")],
        [InlineKeyboardButton("📊 Status", callback_data="menu_status")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ])

# ===== VIDEO MENU =====
def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 Convert", callback_data="video_convert")],
        [InlineKeyboardButton("🖼 Thumbnail Info", callback_data="video_thumb")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, message):

    if not is_joined(client, message.from_user.id):
        message.reply_text(
            "🚫 Join Channel First",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔔 Join Now", url=f"https://t.me/{CHANNEL}")]
            ])
        )
        return

    message.reply_text("🔥 *AniToon PRO Bot*\n\nSelect option:", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(client, query):

    user_id = query.from_user.id
    data = query.data

    if not is_joined(client, user_id):
        safe_edit(query.message, "🚫 Join Channel First")
        return

    # MAIN MENU NAVIGATION
    if data == "back_main":
        safe_edit(query.message, "🏠 Main Menu", main_menu())

    elif data == "menu_rename":
        safe_edit(query.message, "📁 Send a file to rename")

    elif data == "menu_video":
        safe_edit(query.message, "🎬 Video Tools", video_menu())

    elif data == "menu_settings":
        safe_edit(query.message, "⚙ Settings coming soon")

    elif data == "menu_status":
        safe_edit(query.message, f"📊 Queue: {task_queue.qsize()}")

    elif data == "menu_help":
        safe_edit(query.message, "Send file → choose rename → done")

    # VIDEO FEATURES
    elif data == "video_convert":
        safe_edit(query.message, "🎞 Convert feature coming soon")

    elif data == "video_thumb":
        safe_edit(query.message, "🖼 Thumbnail auto used in uploads")

    # RENAME
    elif data == "manual":
        user_steps[user_id] = "rename"
        safe_edit(query.message, "✏ Send new name")

    elif data == "auto":

        if user_id not in user_files:
            safe_edit(query.message, "❌ Session expired")
            return

        file_msg = user_files[user_id]
        name = file_msg.document.file_name
        new_name = smart_name(os.path.splitext(name)[0])

        pos = task_queue.qsize() + 1
        task_queue.put((file_msg, new_name, query.message))

        safe_edit(query.message, f"⏳ Added\n📍 Position: {pos}")

# ===== FILE =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, message):

    if not is_joined(client, message.from_user.id):
        message.reply_text("🚫 Join Channel First")
        return

    user_id = message.from_user.id
    user_files[user_id] = message
    user_steps[user_id] = "choose"

    name = message.document.file_name if message.document else "file"
    suggested = smart_name(os.path.splitext(name)[0])

    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Auto", callback_data="auto"),
            InlineKeyboardButton("✏ Manual", callback_data="manual")
        ]
    ])

    message.reply_text(f"💡 Suggested:\n`{suggested}`", reply_markup=btn)

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message):

    user_id = message.from_user.id

    if user_steps.get(user_id) != "rename":
        return

    file_msg = user_files.get(user_id)
    if not file_msg:
        return

    new_name = message.text.strip()

    pos = task_queue.qsize() + 1
    task_queue.put((file_msg, new_name, message))

    message.reply_text(f"⏳ Added\n📍 Position: {pos}")

# ===== WORKER =====
def worker():
    while True:
        file_msg, new_name, msg = task_queue.get()
        try:
            process_file(file_msg, new_name, msg)
        except Exception as e:
            msg.reply_text(f"❌ {e}")
        task_queue.task_done()

# ===== PROCESS =====
def process_file(file_msg, new_name, msg):

    progress_msg = msg.reply_text("⏳ Starting...", reply_markup=progress_btn())

    last = -1
    start = time.time()

    def progress(c, t):
        nonlocal last
        p = int(c*100/t)

        if p == last:
            return
        last = p

        speed = c / (time.time() - start + 1)
        eta = (t - c) / (speed + 1)

        safe_edit(
            progress_msg,
            f"📥 Downloading...\n\n[{progress_bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n⏳ {int(eta)} sec",
            progress_btn()
        )

    file_path = file_msg.download(progress=progress)

    ext = os.path.splitext(file_path)[1]
    new_file = f"{new_name}{ext}"
    os.rename(file_path, new_file)

    def up(c, t):
        p = int(c*100/t)
        safe_edit(progress_msg, f"📤 Uploading...\n\n[{progress_bar(p)}] {p}%", progress_btn())

    file_msg.reply_document(new_file, caption=f"✅ {new_name}", progress=up)

    try:
        progress_msg.delete()
    except:
        pass

    os.remove(new_file)

# ===== RUN =====
if __name__ == "__main__":

    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 Bot Starting...")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
