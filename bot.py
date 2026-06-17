# ===== ULTIMATE FINAL TELEGRAM BOT (AniToon GOD MAX) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserNotParticipant
from config import *
import os, re, time, threading, json
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
CHANNEL = "Anitoon_edit"
CHANNEL_LINK = "https://t.me/Anitoon_edit"
CHANNEL_POST = "https://t.me/Anitoon_edit/33"
WORKERS = 4
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB

# ===== FOLDERS =====
os.makedirs("thumbs", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

# ===== DATABASE =====
DB_FILE = "db.json"
if not os.path.exists(DB_FILE):
    json.dump({}, open(DB_FILE, "w"))

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

# ===== FLASK =====
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

# ===== JOIN CHECK =====
def is_joined(client, uid):
    try:
        client.get_chat_member(CHANNEL, uid)
        return True
    except UserNotParticipant:
        return False
    except:
        return True

# ===== SMART RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)

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

def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 AniToon's Channel", url=CHANNEL_LINK)]
    ])

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel List", url=CHANNEL_POST)]
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
         InlineKeyboardButton("📦 File Tools", callback_data="filetools")],
        [InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb"),
         InlineKeyboardButton("ℹ Info", callback_data="info")],
        [InlineKeyboardButton("📊 Status", callback_data="status"),
         InlineKeyboardButton("⚙ Settings", callback_data="settings")]
    ])

def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 File→Video", callback_data="f2v"),
         InlineKeyboardButton("📂 Video→File", callback_data="v2f")],
        [InlineKeyboardButton("📷 Screenshot", callback_data="ss"),
         InlineKeyboardButton("🎬 Trim", callback_data="trim")],
        [InlineKeyboardButton("🔊 Mute", callback_data="mute"),
         InlineKeyboardButton("🎧 Extract Audio", callback_data="extract")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def audio_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Convert", callback_data="aconvert"),
         InlineKeyboardButton("🎚 Boost", callback_data="boost")],
        [InlineKeyboardButton("⏱ Trim", callback_data="atrim"),
         InlineKeyboardButton("🔊 Volume", callback_data="volume")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def file_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Zip", callback_data="zip"),
         InlineKeyboardButton("📂 Unzip", callback_data="unzip")],
        [InlineKeyboardButton("📝 Rename", callback_data="rename"),
         InlineKeyboardButton("📑 JSON Format", callback_data="json")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):

    if not is_joined(client, msg.from_user.id):
        msg.reply_text(
            "🚫 You must subscribe the channel to continue",
            reply_markup=join_btn()
        )
        return

    msg.reply_text("🔥 *AniToon Ultimate Bot*\n\nSelect Option:", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(client, q):

    uid = q.from_user.id
    data = q.data

    if not is_joined(client, uid):
        safe_edit(q.message, "🚫 Join first", join_btn())
        return

    if data == "rename":
        safe_edit(q.message, "📁 Send file to rename")

    elif data == "video":
        safe_edit(q.message, "🎬 Video Tools", video_menu())

    elif data == "audio":
        safe_edit(q.message, "🎵 Audio Tools", audio_menu())

    elif data == "filetools":
        safe_edit(q.message, "📦 File Tools", file_menu())

    elif data == "thumb":
        user_steps[uid] = "thumb"
        safe_edit(q.message, "🖼 Send thumbnail image")

    elif data == "info":
        user_steps[uid] = "info"
        safe_edit(q.message, "📥 Send file to get info")

    elif data == "settings":
        safe_edit(q.message, "⚙ Settings\n- Thumbnail\n- Rename Mode")

    elif data == "status":
        safe_edit(q.message, f"📊 Queue: {task_queue.qsize()}\n⚡ Active: {active_tasks}")

    elif data == "back":
        safe_edit(q.message, "🏠 Menu", main_menu())

    elif data == "auto":
        file = user_files.get(uid)
        if not file:
            return

        name = file.document.file_name if file.document else "file"
        new = smart_name(os.path.splitext(name)[0])

        pos = task_queue.qsize() + 1
        task_queue.put((file, new, q.message))

        safe_edit(q.message, f"⏳ Added\n📍 Position: {pos}")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, msg):

    if not is_joined(client, msg.from_user.id):
        msg.reply_text("🚫 Join first", reply_markup=join_btn())
        return

    uid = msg.from_user.id

    # INFO MODE
    if user_steps.get(uid) == "info":
        msg.reply_text(f"""
📂 File Info:
📛 Name: {msg.document.file_name if msg.document else "Media"}
📦 Size: {round(msg.document.file_size/1024/1024,2)} MB
🎬 Type: {msg.media}
        """)
        user_steps.pop(uid)
        return

    user_files[uid] = msg

    name = msg.document.file_name if msg.document else "file"
    sug = smart_name(os.path.splitext(name)[0])

    msg.reply_text(
        f"💡 Suggested:\n`{sug}`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Auto Rename", callback_data="auto")]
        ])
    )

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
            f"📥 Downloading...\n\n[{bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n⏳ {int(eta)} sec",
            progress_btn()
        )

    path = file.download(file_name=f"downloads/{time.time()}", progress=progress)

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
            print("🚀 AniToon Ultimate Bot Started")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
