# ===== AniToons Rename Bot (GOD MODE FINAL SYSTEM) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *

import os, re, time, threading, subprocess
from queue import Queue

# ===== CORE SETTINGS =====
WORKERS = 10
EDIT_DELAY = 1.2   # avoid flood
MAX_SIZE = 2 * 1024 * 1024 * 1024

# ===== FOLDERS =====
for f in ["downloads", "outputs", "thumbs"]:
    os.makedirs(f, exist_ok=True)

# ===== BOT =====
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=200
)

# ===== GLOBAL DATA =====
task_queue = Queue()
user_mode = {}
user_files = {}
saved_name = {}
last_edit = {}

# ===== UTIL =====
def safe_edit(msg, text):
    now = time.time()
    if msg.id not in last_edit or now - last_edit[msg.id] > EDIT_DELAY:
        try:
            msg.edit_text(text)
            last_edit[msg.id] = now
        except:
            pass

def clean_name(name):
    name = re.sub(r'@\w+|\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title() or "File"

def get_name(file):
    return file.document.file_name if file.document else "file"

# ===== UI =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename")],
        [InlineKeyboardButton("🎬 Convert", callback_data="convert")],
        [InlineKeyboardButton("⚙ Save Name", callback_data="save")],
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(_, msg):
    msg.reply_text("🚀 Ready\nSend files after choosing option", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def cb(_, q):
    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "rename":
        user_mode[uid] = "rename"
        user_files[uid] = []
        q.message.reply_text("📁 Send files now")

    elif data == "convert":
        user_mode[uid] = "convert"
        q.message.reply_text("🎬 Send file/video")

    elif data == "save":
        user_mode[uid] = "save"
        q.message.reply_text("✏ Send name to save")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def files(_, msg):

    uid = msg.from_user.id
    mode = user_mode.get(uid)

    if msg.document and msg.document.file_size > MAX_SIZE:
        msg.reply_text("❌ Too large")
        return

    if mode == "rename":
        user_files.setdefault(uid, []).append(msg)
        msg.reply_text(f"📦 Added ({len(user_files[uid])})\nSend name now")

    elif mode == "convert":
        task_queue.put((msg, "convert", uid))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text(_, msg):

    uid = msg.from_user.id
    mode = user_mode.get(uid)

    if mode == "save":
        saved_name[uid] = msg.text
        msg.reply_text("✅ Saved")

    elif mode == "rename":
        for f in user_files.get(uid, []):
            name = msg.text or saved_name.get(uid) or clean_name(get_name(f))
            task_queue.put((f, name, uid))

# ===== WORKER =====
def worker():
    while True:
        file, name, uid = task_queue.get()
        try:
            process(file, name, uid)
        except:
            try:
                file.reply_text("❌ Failed")
            except:
                pass
        task_queue.task_done()

# ===== PROCESS ENGINE =====
def process(file, name, uid):

    msg = file.reply_text(f"⏳ Queue: {task_queue.qsize()}")

    # ===== DOWNLOAD =====
    start = time.time()

    def dprog(c, t):
        p = int(c * 100 / t)
        speed = c / (time.time() - start + 1)
        safe_edit(msg, f"⬇ Download {p}%\n⚡ {round(speed/1024/1024,2)} MB/s")

    path = file.download(file_name=f"downloads/{time.time()}", progress=dprog)

    if not path:
        return

    # ===== MODE =====
    mode = user_mode.get(uid)

    safe_edit(msg, "⚙ Processing...")

    # ===== CONVERT =====
    if name == "convert":
        if path.endswith(".mp4"):
            out = f"outputs/{time.time()}.mkv"
            subprocess.run(["ffmpeg","-i",path,"-c","copy",out])
        else:
            out = f"outputs/{time.time()}.mp4"
            subprocess.run(["ffmpeg","-i",path,out])
        path = out

    # ===== THUMB =====
    thumb = f"thumbs/{time.time()}.jpg"
    subprocess.run([
        "ffmpeg","-i",path,
        "-ss","2",
        "-vframes","1",
        thumb
    ])

    # ===== RENAME =====
    ext = os.path.splitext(path)[1]
    new = f"outputs/{name}{ext}"
    os.rename(path, new)

    # ===== UPLOAD =====
    def uprog(c, t):
        p = int(c * 100 / t)
        safe_edit(msg, f"⬆ Upload {p}%")

    # ===== SEND FIXED =====
    try:
        if ext in [".mp4", ".mkv"]:
            file.reply_video(
                new,
                caption=f"✅ {name}",
                thumb=thumb,
                progress=uprog
            )
        else:
            file.reply_document(
                new,
                caption=f"✅ {name}",
                thumb=thumb,
                progress=uprog
            )
    except:
        file.reply_document(new, caption=f"✅ {name}")

    os.remove(new)
    safe_edit(msg, "✅ Done")

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    while True:
        try:
            print("🚀 GOD MODE RUNNING")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
