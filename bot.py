# ===== AniToons Rename Bot (FINAL FIXED + SAVED NAME + FAST FLOW) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, subprocess, json
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
CHANNEL_POST = "https://t.me/Anitoon_edit/33"
WORKERS = 6

# ===== FOLDERS =====
os.makedirs("thumbs", exist_ok=True)
os.makedirs("downloads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# ===== DATABASE (LOCAL SIMPLE) =====
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

# ===== WEB =====
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ===== BOT =====
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=120)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_mode = {}
active_tasks = 0

# ===== SMART RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title() or "AniToon_File"

# ===== UI =====
def bar(p):
    return "█"*int(p/10) + "░"*(10-int(p/10))

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename")],
        [InlineKeyboardButton("🎬 Convert", callback_data="convert")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")]
    ])

def rename_menu(uid):
    saved = get_user(uid).get("saved_name")

    btn = [
        [InlineKeyboardButton("⚡ Auto Rename", callback_data="auto")],
        [InlineKeyboardButton("✏ Manual Rename", callback_data="manual")]
    ]

    if saved:
        btn.append([InlineKeyboardButton("📌 Use Saved Name", callback_data="saved")])
    else:
        btn.append([InlineKeyboardButton("➕ Set Saved Name", callback_data="setname")])

    btn.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(btn)

def convert_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 File → Video", callback_data="f2v")],
        [InlineKeyboardButton("📂 Video → File", callback_data="v2f")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Change Saved Name", callback_data="setname")],
        [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):
    msg.reply_text(
        "🔥 **AniToons Bot**\n\n"
        "⚡ Rename + Convert\n"
        "📦 Fast Processing System\n\n"
        "👇 Choose:",
        reply_markup=main_menu()
    )

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(client, q):

    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "rename":
        user_mode[uid] = "waiting_file"
        q.message.edit_text("📁 Send file first")

    elif data == "convert":
        user_mode[uid] = "convert"
        q.message.edit_text("🎬 Choose option", reply_markup=convert_menu())

    elif data == "settings":
        q.message.edit_text("⚙ Settings", reply_markup=settings_menu())

    elif data == "setname":
        user_mode[uid] = "setname"
        q.message.edit_text("📌 Send name to save")

    elif data == "manual":
        user_mode[uid] = "manual"
        q.message.edit_text("✏ Send new name")

    elif data == "auto":
        file = user_files.get(uid)
        if file:
            name = smart_name(file.document.file_name)
            task_queue.put((file, name))

    elif data == "saved":
        file = user_files.get(uid)
        saved = get_user(uid).get("saved_name")
        if file and saved:
            task_queue.put((file, saved))

    elif data == "f2v":
        user_mode[uid] = "f2v"
        q.message.edit_text("🎞 Send file")

    elif data == "v2f":
        user_mode[uid] = "v2f"
        q.message.edit_text("📂 Send video")

    elif data == "thumb":
        user_mode[uid] = "thumb"
        q.message.edit_text("🖼 Send thumbnail image")

    elif data == "back":
        user_mode[uid] = None
        q.message.edit_text("🏠 Menu", reply_markup=main_menu())

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video)
def file_handler(client, msg):

    uid = msg.from_user.id
    mode = user_mode.get(uid)

    # CONVERT
    if mode in ["f2v", "v2f"]:
        task_queue.put((msg, "converted"))
        return

    # RENAME FLOW
    if mode == "waiting_file":
        user_files[uid] = msg
        msg.reply_text(
            "📂 File received\n\nChoose rename option:",
            reply_markup=rename_menu(uid)
        )
        return

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text_handler(client, msg):

    uid = msg.from_user.id

    if user_mode.get(uid) == "manual":
        file = user_files.get(uid)
        if file:
            task_queue.put((file, msg.text.strip()))

    elif user_mode.get(uid) == "setname":
        set_user(uid, "saved_name", msg.text.strip())
        msg.reply_text("✅ Saved name updated")

# ===== THUMB =====
@app.on_message(filters.photo)
def thumb(client, msg):

    uid = msg.from_user.id

    if user_mode.get(uid) != "thumb":
        return

    path = msg.download(f"thumbs/{uid}.jpg")
    set_user(uid, "thumb", path)
    msg.reply_text("✅ Thumbnail saved")

# ===== WORKER =====
def worker():
    global active_tasks

    while True:
        file, name = task_queue.get()
        active_tasks += 1

        try:
            process(file, name)
        except Exception as e:
            file.reply_text(f"❌ {e}")

        active_tasks -= 1
        task_queue.task_done()

# ===== AUTO THUMB =====
def auto_thumb(video, uid):
    path = f"thumbs/{uid}_auto.jpg"
    subprocess.run([
        "ffmpeg", "-i", video,
        "-ss", "00:00:02",
        "-vframes", "1",
        path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return path if os.path.exists(path) else None

# ===== PROCESS =====
def process(file, name):

    uid = file.from_user.id
    mode = user_mode.get(uid)

    pmsg = file.reply_text("⬇ Downloading...")

    start = time.time()

    def progress(c, t):
        p = int(c*100/t)
        speed = c/(time.time()-start+1)
        pmsg.edit_text(f"⬇ Downloading\n[{bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s")

    path = file.download(file_name=f"downloads/{time.time()}", progress=progress)

    # CONVERT
    if mode == "f2v":
        pmsg.edit_text("🔄 Converting to video...")
        out = f"outputs/{time.time()}.mp4"
        subprocess.run(["ffmpeg","-i",path,"-preset","ultrafast",out])
        path = out

    elif mode == "v2f":
        pmsg.edit_text("🔄 Converting to file...")
        out = f"outputs/{time.time()}.mkv"
        subprocess.run(["ffmpeg","-i",path,"-c","copy",out])
        path = out

    ext = os.path.splitext(path)[1]
    new_file = f"outputs/{name}{ext}"
    os.rename(path, new_file)

    # THUMB
    thumb = get_user(uid).get("thumb")
    if not thumb and ext in [".mp4", ".mkv"]:
        thumb = auto_thumb(new_file, uid)

    # UPLOAD
    pmsg.edit_text("⬆ Uploading...")

    def up(c, t):
        p = int(c*100/t)
        pmsg.edit_text(f"⬆ Uploading\n[{bar(p)}] {p}%")

    if ext in [".mp4", ".mkv"]:
        file.reply_video(new_file, caption=f"✅ {name}", thumb=thumb, progress=up)
    else:
        file.reply_document(new_file, caption=f"✅ {name}", progress=up)

    pmsg.delete()
    os.remove(new_file)

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 Bot Started")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
