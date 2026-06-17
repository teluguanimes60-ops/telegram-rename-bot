# ===== ULTIMATE FINAL TELEGRAM BOT (AniToon GOD MAX FIXED) =====

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

# ===== JOIN CHECK (FIXED) =====
def is_joined(client, uid):
    try:
        member = client.get_chat_member(CHANNEL, uid)
        return member.status in ["member", "administrator", "creator"]
    except UserNotParticipant:
        return False
    except:
        return False

# ===== SMART RENAME (FIXED PRO) =====
def smart_name(name):

    # remove @words
    name = re.sub(r'@\w+', '', name)

    # remove brackets like [@abc] fully
    name = re.sub(r'\[.*?\]', '', name)

    # remove () content
    name = re.sub(r'\(.*?\)', '', name)

    # remove urls
    name = re.sub(r'https?://\S+|www\.\S+', '', name)

    # KEEP QUALITY (important)
    # clean symbols
    name = re.sub(r'[._\-]', ' ', name)

    # remove extra spaces
    name = re.sub(r'\s+', ' ', name)

    name = name.strip()

    # remove useless last word (garbage)
    words = name.split()
    if len(words) > 3:
        words = words[:-1]

    name = " ".join(words)

    return name.title() if name else "AniToon_File"

# ===== PROGRESS BAR (PRO LOOK) =====
def progress_bar(p):
    filled = int(p / 5)
    return "▰" * filled + "▱" * (20 - filled)

def format_time(seconds):
    return f"{int(seconds//60)}m {int(seconds%60)}s"

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 AniToon's Channel List", url=CHANNEL_POST)]
    ])

def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 AniToon's Channel", url=CHANNEL_LINK)]
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
         InlineKeyboardButton("🎬 Video", callback_data="video")],
        [InlineKeyboardButton("🎵 Audio", callback_data="audio"),
         InlineKeyboardButton("📦 Files", callback_data="files")],
        [InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb"),
         InlineKeyboardButton("ℹ Info", callback_data="info")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):

    if not is_joined(client, msg.from_user.id):
        msg.reply_text(
            "🚫 **You must subscribe the channel to continue**",
            reply_markup=join_btn()
        )
        return

    msg.reply_text(
        "🔥 *AniToon Ultimate Bot*\n\nSelect Option:",
        reply_markup=main_menu()
    )

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(client, q):

    uid = q.from_user.id
    data = q.data

    if not is_joined(client, uid):
        safe_edit(
            q.message,
            "🚫 You must subscribe to continue",
            join_btn()
        )
        return

    if data == "rename":
        safe_edit(q.message, "📁 Send file to rename")

    elif data == "thumb":
        user_steps[uid] = "thumb"
        safe_edit(q.message, "🖼 Send thumbnail image")

    elif data == "info":
        user_steps[uid] = "info"
        safe_edit(q.message, "📥 Send file to get full info")

    elif data == "status":
        safe_edit(
            q.message,
            f"📊 Queue: {task_queue.qsize()}\n⚡ Active: {active_tasks}"
        )

    elif data == "auto":
        file = user_files.get(uid)
        if not file:
            return

        name = file.document.file_name if file.document else "file"
        new = smart_name(os.path.splitext(name)[0])

        pos = task_queue.qsize() + 1
        task_queue.put((file, new, q.message))

        safe_edit(q.message, f"⏳ Added to Queue\n📍 Position: {pos}")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, msg):

    if not is_joined(client, msg.from_user.id):
        msg.reply_text(
            "🚫 Join channel first",
            reply_markup=join_btn()
        )
        return

    uid = msg.from_user.id

    # INFO MODE
    if user_steps.get(uid) == "info":
        size = round((msg.document.file_size if msg.document else 0)/1024/1024,2)

        msg.reply_text(f"""
📂 **File Info**
📛 Name: {msg.document.file_name if msg.document else "Media"}
📦 Size: {size} MB
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
    msg.reply_text("✅ Thumbnail Saved")

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

    start_time = time.time()

    pmsg = msg.reply_text("⏳ Initializing...", reply_markup=progress_btn())

    def progress(c, t):
        percent = int(c * 100 / t)
        speed = c / (time.time() - start_time + 1)
        eta = (t - c) / (speed + 1)

        safe_edit(
            pmsg,
            f"""
📥 **Downloading**

{progress_bar(percent)} {percent}%

⚡ Speed: {round(speed/1024/1024,2)} MB/s
⏳ ETA: {format_time(eta)}
            """,
            progress_btn()
        )

    path = file.download(
        file_name=f"downloads/{time.time()}",
        progress=progress
    )

    ext = os.path.splitext(path)[1]
    new_file = f"{name}{ext}"
    os.rename(path, new_file)

    def upload(c, t):
        percent = int(c * 100 / t)

        safe_edit(
            pmsg,
            f"""
📤 **Uploading**

{progress_bar(percent)} {percent}%
            """,
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
