# ===== AniToons Rename Bot (ULTIMATE USER FLOW VERSION) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
from flask import Flask
import os, re, time, threading, subprocess
from queue import Queue

# ===== SETTINGS =====
WORKERS = 8
CHANNEL_LINK = "https://t.me/Anitoon_edit/33"

# ===== FOLDERS =====
BASE = os.getcwd()
DOWNLOAD = f"{BASE}/downloads"
OUTPUT = f"{BASE}/outputs"
THUMB = f"{BASE}/thumbs"

for p in [DOWNLOAD, OUTPUT, THUMB]:
    os.makedirs(p, exist_ok=True)

# ===== WEB (RENDER FIX) =====
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

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
saved_names = {}
user_thumb = {}

# ===== SMART NAME =====
def smart_name(name):
    name = re.sub(r'@\w+|\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip().title()

# ===== UI =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename")],
        [InlineKeyboardButton("🎬 Video", callback_data="video")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("📢 AniToon's List", url=CHANNEL_LINK)]
    ])

def rename_options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Auto", callback_data="auto")],
        [InlineKeyboardButton("✏ Manual", callback_data="manual")],
        [InlineKeyboardButton("📌 Saved", callback_data="saved")]
    ])

def video_options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 File → Video", callback_data="f2v")],
        [InlineKeyboardButton("🎬 Video → File", callback_data="v2f")]
    ])

def thumb_options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Auto Thumbnail", callback_data="auto_thumb")],
        [InlineKeyboardButton("🖼 Saved Thumbnail", callback_data="saved_thumb")]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Change Saved Name", callback_data="setname")],
        [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="setthumb")],
        [InlineKeyboardButton("👁 View Thumbnail", callback_data="viewthumb")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(_, m):
    m.reply_text("🚀 **AniToons Ultimate Bot**", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def cb(_, q):

    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "rename":
        user_mode[uid] = "wait_file"
        q.message.reply_text("📁 Send file to rename")

    elif data == "video":
        user_mode[uid] = "video_select"
        q.message.reply_text("🎬 Choose convert type", reply_markup=video_options())

    elif data == "settings":
        q.message.reply_text("⚙ Settings Panel", reply_markup=settings_menu())

    elif data == "auto":
        f = user_files.get(uid)
        task_queue.put((f, smart_name(get_name(f)), uid, "rename"))

    elif data == "manual":
        user_mode[uid] = "manual_name"
        q.message.reply_text("✏ Send new name")

    elif data == "saved":
        f = user_files.get(uid)
        name = saved_names.get(uid, "File")
        task_queue.put((f, name, uid, "rename"))

    elif data == "f2v":
        user_mode[uid] = "f2v"
        q.message.reply_text("🎬 Send file")
        
    elif data == "v2f":
        user_mode[uid] = "v2f"
        q.message.reply_text("📂 Send video")

    elif data in ["f2v", "v2f"]:
        q.message.reply_text("Choose Thumbnail", reply_markup=thumb_options())

    elif data == "auto_thumb":
        user_mode[uid] += "_auto"

    elif data == "saved_thumb":
        user_mode[uid] += "_saved"

    elif data == "setname":
        user_mode[uid] = "setname"
        q.message.reply_text("📌 Send new saved name")

    elif data == "setthumb":
        user_mode[uid] = "setthumb"
        q.message.reply_text("🖼 Send thumbnail image")

    elif data == "viewthumb":
        t = user_thumb.get(uid)
        if t:
            q.message.reply_photo(t)
        else:
            q.message.reply_text("❌ No thumbnail")

# ===== FILE =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    if mode == "wait_file":
        user_files[uid] = m
        m.reply_text("⚙ Choose rename type", reply_markup=rename_options())

    elif mode in ["f2v_auto", "f2v_saved", "v2f_auto", "v2f_saved"]:
        task_queue.put((m, "convert", uid, mode))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    if mode == "manual_name":
        f = user_files.get(uid)
        task_queue.put((f, m.text, uid, "rename"))

    elif mode == "setname":
        saved_names[uid] = m.text
        m.reply_text("✅ Saved Name Updated")

# ===== THUMB =====
@app.on_message(filters.photo)
def thumb(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) == "setthumb":
        path = m.download(f"{THUMB}/{uid}.jpg")
        user_thumb[uid] = path
        m.reply_text("✅ Thumbnail Saved")

# ===== NAME =====
def get_name(f):
    return f.document.file_name if f.document else "file"

# ===== WORKER =====
def worker():
    while True:
        file, name, uid, mode = task_queue.get()
        try:
            process(file, name, uid, mode)
        except:
            pass
        task_queue.task_done()

# ===== PROCESS =====
def process(file, name, uid, mode):

    msg = file.reply_text("⏳ Starting...")

    start = time.time()

    def circle(p):
        icons = ["◐","◓","◑","◒"]
        return icons[p % 4]

    def dprog(c, t):
        p = int(c*100/t)
        msg.edit_text(f"{circle(p)} Downloading {p}%")

    path = file.download(progress=dprog)

    msg.edit_text("⚙ Processing...")

    # CONVERT
    if "convert" in mode:
        if path.endswith(".mp4"):
            out = f"{OUTPUT}/{time.time()}.mkv"
            subprocess.run(["ffmpeg","-i",path,"-c","copy",out])
        else:
            out = f"{OUTPUT}/{time.time()}.mp4"
            subprocess.run(["ffmpeg","-i",path,out])
        path = out

    # THUMB
    if "auto" in mode:
        thumb = f"{THUMB}/{time.time()}.jpg"
        subprocess.run(["ffmpeg","-i",path,"-ss","2","-vframes","1",thumb])
    else:
        thumb = user_thumb.get(uid)

    ext = os.path.splitext(path)[1]
    new = f"{OUTPUT}/{name}{ext}"
    os.rename(path, new)

    def uprog(c, t):
        p = int(c*100/t)
        msg.edit_text(f"⬆ Uploading {p}%")

    if ext in [".mp4",".mkv"]:
        file.reply_video(new, caption=f"✅ {name}", thumb=thumb, progress=uprog)
    else:
        file.reply_document(new, caption=f"✅ {name}", thumb=thumb, progress=uprog)

    os.remove(new)
    msg.delete()

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 Running Ultimate Bot")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
