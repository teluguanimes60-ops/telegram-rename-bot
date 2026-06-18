# ===== AniToons Rename Bot (GOD MODE ULTRA SYSTEM - FINAL FIXED) =====
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, subprocess
from queue import Queue

# ===== SETTINGS =====
WORKERS = 12

# ===== WEB SERVER (RENDER FIX) =====
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

# ===== FOLDERS =====
BASE = os.getcwd()
DOWNLOAD = f"{BASE}/downloads"
OUTPUT = f"{BASE}/outputs"
THUMB = f"{BASE}/thumbs"
SCREEN = f"{BASE}/screens"

for p in [DOWNLOAD, OUTPUT, THUMB, SCREEN]:
    os.makedirs(p, exist_ok=True)

# ===== BOT =====
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=200
)

# ===== DATA =====
task_queue = Queue()
user_mode = {}
user_files = {}
saved_name = {}
active_tasks = 0

# ===== SMART RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+|\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title() or "File"

# ===== UI =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename")],
        [InlineKeyboardButton("🎬 Convert", callback_data="convert")],
        [InlineKeyboardButton("📸 Screenshots", callback_data="ss")],
        [InlineKeyboardButton("⚙ Saved Name", callback_data="setname")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(_, m):
    m.reply_text("🚀 Bot Ready\n\nChoose option below:", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def cb(_, q):

    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "rename":
        user_mode[uid] = "rename"
        user_files[uid] = []
        q.message.reply_text("📁 Send files to rename")

    elif data == "convert":
        user_mode[uid] = "convert"
        q.message.reply_text("🎬 Send file/video")

    elif data == "ss":
        user_mode[uid] = "ss"
        q.message.reply_text("📸 Send video")

    elif data == "setname":
        user_mode[uid] = "setname"
        q.message.reply_text("📌 Send name to save")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    if mode == "rename":
        user_files.setdefault(uid, []).append(m)
        m.reply_text("✅ File added\nSend name OR wait for auto rename")

    elif mode == "convert":
        task_queue.put((m, "convert", uid))

    elif mode == "ss":
        task_queue.put((m, "ss", uid))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    if mode == "setname":
        saved_name[uid] = m.text
        m.reply_text("✅ Saved for all files")

    elif mode == "rename":
        for f in user_files.get(uid, []):
            name = m.text or saved_name.get(uid) or smart_name(get_name(f))
            task_queue.put((f, name, uid))

# ===== NAME =====
def get_name(f):
    return f.document.file_name if f.document else "file"

# ===== WORKER =====
def worker():
    global active_tasks

    while True:
        file, name, uid = task_queue.get()
        active_tasks += 1

        try:
            process(file, name, uid)
        except:
            try:
                file.reply_text("❌ Failed")
            except:
                pass

        active_tasks -= 1
        task_queue.task_done()

# ===== PROCESS =====
def process(file, name, uid):

    msg = file.reply_text("⏳ Starting...")
    start = time.time()

    # ===== DOWNLOAD =====
    def dprog(c, t):
        p = int(c * 100 / t)
        speed = c / (time.time() - start + 1)
        eta = (t - c) / (speed + 1)

        msg.edit_text(
            f"⬇ Downloading\n"
            f"Progress: {p}%\n"
            f"Speed: {round(speed/1024/1024,2)} MB/s\n"
            f"ETA: {int(eta)} sec"
        )

    path = file.download(file_name=f"{DOWNLOAD}/{time.time()}", progress=dprog)

    if not path:
        return

    msg.edit_text("⚙ Processing...")

    mode = user_mode.get(uid)

    # ===== CONVERT =====
    if name == "convert":
        if path.endswith(".mp4"):
            out = f"{OUTPUT}/{time.time()}.mkv"
            subprocess.run(["ffmpeg", "-y", "-i", path, "-c", "copy", out])
        else:
            out = f"{OUTPUT}/{time.time()}.mp4"
            subprocess.run(["ffmpeg", "-y", "-i", path, out])
        path = out

    # ===== SCREENSHOTS =====
    elif name == "ss":
        for i in range(1, 6):
            img = f"{SCREEN}/{time.time()}_{i}.jpg"
            subprocess.run([
                "ffmpeg","-y","-i",path,
                "-ss",str(i*2),
                "-vframes","1",img
            ])
            file.reply_photo(img)
        return

    # ===== AUTO THUMB =====
    thumb = f"{THUMB}/{time.time()}.jpg"
    subprocess.run([
        "ffmpeg","-y","-i",path,
        "-ss","3",
        "-vframes","1",thumb
    ])

    # ===== RENAME =====
    ext = os.path.splitext(path)[1]
    new_file = f"{OUTPUT}/{name}{ext}"
    os.rename(path, new_file)

    msg.edit_text("⬆ Uploading...")

    # ===== UPLOAD =====
    up_start = time.time()

    def uprog(c, t):
        p = int(c * 100 / t)
        speed = c / (time.time() - up_start + 1)

        msg.edit_text(
            f"⬆ Uploading\n"
            f"Progress: {p}%\n"
            f"Speed: {round(speed/1024/1024,2)} MB/s"
        )

    if ext in [".mp4", ".mkv"]:
        file.reply_video(
            new_file,
            caption=f"✅ {name}",
            thumb=thumb,
            progress=uprog
        )
    else:
        file.reply_document(
            new_file,
            caption=f"✅ {name}",
            thumb=thumb,
            progress=uprog
        )

    try:
        os.remove(new_file)
        os.remove(thumb)
    except:
        pass

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    # 🔥 REQUIRED FOR RENDER
    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 GOD MODE RUNNING")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
