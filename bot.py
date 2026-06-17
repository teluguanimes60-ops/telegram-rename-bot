# ===== ULTIMATE ADVANCED TELEGRAM BOT (FINAL VERSION) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, json
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
WORKERS = 4
DB_FILE = "db.json"

# ===== STORAGE =====
if not os.path.exists("thumbs"):
    os.mkdir("thumbs")

if not os.path.exists(DB_FILE):
    json.dump({}, open(DB_FILE, "w"))

# ===== DATABASE =====
def load_db():
    return json.load(open(DB_FILE))

def save_db(data):
    json.dump(data, open(DB_FILE, "w"))

def get_user(uid):
    return load_db().get(str(uid), {})

def set_user(uid, key, value):
    db = load_db()
    if str(uid) not in db:
        db[str(uid)] = {}
    db[str(uid)][key] = value
    save_db(db)

# ===== FLASK (RENDER) =====
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=10000)

# ===== BOT =====
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_steps = {}
active_tasks = 0

# ===== SMART RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+|www\.\S+', '', name)

    words = name.split()
    if len(words) > 3:
        words = words[:-1]
    name = " ".join(words)

    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip().title() or "AniToon_File"

# ===== UI =====
def bar(p):
    return "█" * int(p/10) + "░" * (10-int(p/10))

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 AniToon's Channel List", url="https://t.me/Anitoon_edit/33")]
    ])

def safe_edit(msg, text, btn=None):
    try:
        msg.edit_text(text, reply_markup=btn)
    except:
        pass

# ===== MENUS =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename"),
         InlineKeyboardButton("🎬 Video Tools", callback_data="video")],
        [InlineKeyboardButton("🎵 Audio Tools", callback_data="audio"),
         InlineKeyboardButton("📦 File Tools", callback_data="file")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings"),
         InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("ℹ Info", callback_data="info"),
         InlineKeyboardButton("❓ Help", callback_data="help")]
    ])

def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 Convert Video", callback_data="v_convert")],
        [InlineKeyboardButton("📸 Screenshots", callback_data="v_ss")],
        [InlineKeyboardButton("✂ Trim Video", callback_data="v_trim")],
        [InlineKeyboardButton("🔇 Mute Audio", callback_data="v_mute")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def audio_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 Convert Audio", callback_data="a_convert")],
        [InlineKeyboardButton("🔊 Volume Boost", callback_data="a_boost")],
        [InlineKeyboardButton("🎼 Equalizer", callback_data="a_eq")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def file_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Create Zip", callback_data="zip")],
        [InlineKeyboardButton("📂 Extract Zip", callback_data="unzip")],
        [InlineKeyboardButton("📝 Rename File", callback_data="rename")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):
    msg.reply_text(
        "🔥 **AniToon Ultimate Bot**\n\nUse buttons below:",
        reply_markup=main_menu()
    )

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(client, q):
    uid = q.from_user.id
    data = q.data

    if data == "back":
        safe_edit(q.message, "🏠 Main Menu", main_menu())

    elif data == "rename":
        safe_edit(q.message, "📁 Send file to rename")

    elif data == "video":
        safe_edit(q.message, "🎬 Video Tools", video_menu())

    elif data == "audio":
        safe_edit(q.message, "🎵 Audio Tools", audio_menu())

    elif data == "file":
        safe_edit(q.message, "📦 File Tools", file_menu())

    elif data == "settings":
        user_steps[uid] = "thumb"
        safe_edit(q.message, "📷 Send thumbnail to save")

    elif data == "status":
        safe_edit(q.message, f"📊 Queue: {task_queue.qsize()}\n⚡ Active: {active_tasks}")

    elif data == "info":
        user_steps[uid] = "info"
        safe_edit(q.message, "📤 Send file to get info")

    elif data == "help":
        safe_edit(q.message, "Send file → choose action → done")

    elif data == "auto":
        file = user_files.get(uid)
        if not file:
            return

        name = file.document.file_name if file.document else "file"
        new = smart_name(os.path.splitext(name)[0])

        pos = task_queue.qsize() + 1
        task_queue.put((file, new, q.message))
        safe_edit(q.message, f"⏳ Added to queue\n📍 Position: {pos}")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, msg):

    uid = msg.from_user.id
    user_files[uid] = msg

    name = msg.document.file_name if msg.document else "file"
    sug = smart_name(os.path.splitext(name)[0])

    msg.reply_text(
        f"💡 Suggested:\n`{sug}`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Auto Rename", callback_data="auto")]
        ])
    )

# ===== INFO =====
@app.on_message(filters.document & filters.private)
def info_handler(client, msg):

    uid = msg.from_user.id

    if user_steps.get(uid) != "info":
        return

    file = msg.document
    size = round(file.file_size / (1024*1024), 2)

    msg.reply_text(
        f"📄 File Info:\n\n"
        f"📛 Name: {file.file_name}\n"
        f"📦 Size: {size} MB\n"
        f"🧾 MIME: {file.mime_type}"
    )

    user_steps.pop(uid)

# ===== THUMB =====
@app.on_message(filters.photo)
def save_thumb(client, msg):

    uid = msg.from_user.id
    if user_steps.get(uid) != "thumb":
        return

    path = msg.download(f"thumbs/{uid}.jpg")
    set_user(uid, "thumb", path)

    user_steps.pop(uid)
    msg.reply_text("✅ Thumbnail saved")

# ===== WORKER =====
def worker():
    global active_tasks

    while True:
        file, name, msg = task_queue.get()
        active_tasks += 1

        try:
            process(file, name, msg)
        except Exception as e:
            msg.reply_text(f"❌ {e}")

        active_tasks -= 1
        task_queue.task_done()

# ===== PROCESS =====
def process(file, name, msg):

    uid = file.from_user.id
    thumb = get_user(uid).get("thumb")

    pmsg = msg.reply_text("⏳ Starting...", reply_markup=progress_btn())

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
            pmsg,
            f"📥 Downloading...\n\n"
            f"[{bar(p)}] {p}%\n"
            f"⚡ {round(speed/1024/1024,2)} MB/s\n"
            f"⏳ {int(eta)} sec",
            progress_btn()
        )

    path = file.download(progress=progress)

    ext = os.path.splitext(path)[1]
    new_file = f"{name}{ext}"
    os.rename(path, new_file)

    def upload(c, t):
        p = int(c*100/t)
        safe_edit(
            pmsg,
            f"📤 Uploading...\n\n[{bar(p)}] {p}%",
            progress_btn()
        )

    file.reply_document(
        new_file,
        caption=f"✅ {name}",
        thumb=thumb if thumb else None,
        progress=upload
    )

    try:
        pmsg.delete()
    except:
        pass

    os.remove(new_file)

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 BOT STARTED")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
