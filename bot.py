# ===== AniToons Rename Bot (ULTRA STABLE PRO VERSION) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from flask import Flask
from config import *
import os, re, time, threading, subprocess
from queue import Queue

# ===== CONFIG =====
WORKERS = 5
CHANNEL = "https://t.me/Anitoon_edit/33"

# ===== FOLDERS =====
BASE = os.getcwd()
DOWNLOAD = f"{BASE}/downloads"
OUTPUT = f"{BASE}/outputs"
THUMB = f"{BASE}/thumbs"

for p in [DOWNLOAD, OUTPUT, THUMB]:
    os.makedirs(p, exist_ok=True)

# ===== WEB (FOR RENDER) =====
web = Flask(__name__)

@web.route("/")
def home():
    return "AniToons Bot Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ===== BOT =====
app = Client("AniToonsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== DATA =====
queue = Queue()
user_mode = {}
user_file = {}
saved_name = {}
user_thumb_mode = {}
user_saved_thumb = {}

# ===== UTILS =====
def smart(name):
    name = re.sub(r'@\w+|\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip().title() or "File"

def progress_bar(p):
    return "█"*int(p/10) + "░"*(10-int(p/10))

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 AniToon's List", url=CHANNEL)]
    ])

# ===== UI =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename"),
         InlineKeyboardButton("🎬 Convert", callback_data="convert")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("📢 AniToon's List", url=CHANNEL)]
    ])

def rename_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Auto Rename", callback_data="auto")],
        [InlineKeyboardButton("✏ Manual Rename", callback_data="manual")],
        [InlineKeyboardButton("📌 Saved Name", callback_data="saved")]
    ])

def convert_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 File → Video", callback_data="f2v")],
        [InlineKeyboardButton("🎬 Video → File", callback_data="v2f")]
    ])

def thumb_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Auto Thumbnail", callback_data="auto_thumb")],
        [InlineKeyboardButton("🖼 Saved Thumbnail", callback_data="saved_thumb")]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Save Name", callback_data="setname")],
        [InlineKeyboardButton("🖼 Save Thumbnail", callback_data="setthumb")],
        [InlineKeyboardButton("👁 View Thumbnail", callback_data="viewthumb")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(_, m):
    m.reply_text(
        "✨ **AniToons Rename Bot**\n\n"
        "⚡ Fast Rename | 🎬 Convert | 🖼 Thumbnail\n\n"
        "👇 Choose Option",
        reply_markup=main_menu()
    )

# ===== BUTTON HANDLER =====
@app.on_callback_query()
def cb(_, q):
    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "rename":
        user_mode[uid] = "wait_file"
        q.message.reply_text("📤 Send File to Rename")

    elif data == "auto":
        file = user_file.get(uid)
        if file:
            name = smart(file.document.file_name if file.document else "file")
            queue.put((file, name, uid, "rename"))

    elif data == "manual":
        user_mode[uid] = "manual"
        q.message.reply_text("✏ Send new name")

    elif data == "saved":
        file = user_file.get(uid)
        name = saved_name.get(uid, "File")
        queue.put((file, name, uid, "rename"))

    elif data == "convert":
        user_mode[uid] = "convert"
        q.message.reply_text("🎬 Choose option", reply_markup=convert_menu())

    elif data == "f2v":
        user_mode[uid] = "thumb_select"
        q.message.reply_text("🖼 Select Thumbnail", reply_markup=thumb_menu())

    elif data == "auto_thumb":
        user_thumb_mode[uid] = "auto"
        user_mode[uid] = "f2v"
        q.message.reply_text("📤 Send File")

    elif data == "saved_thumb":
        if uid not in user_saved_thumb:
            user_mode[uid] = "setthumb"
            q.message.reply_text("📸 Send Thumbnail First")
        else:
            user_thumb_mode[uid] = "saved"
            user_mode[uid] = "f2v"
            q.message.reply_text("📤 Send File")

    elif data == "settings":
        q.message.reply_text("⚙ Settings", reply_markup=settings_menu())

    elif data == "setname":
        user_mode[uid] = "setname"
        q.message.reply_text("✏ Send Name")

    elif data == "setthumb":
        user_mode[uid] = "setthumb"
        q.message.reply_text("📸 Send Thumbnail")

    elif data == "viewthumb":
        if uid in user_saved_thumb:
            q.message.reply_photo(user_saved_thumb[uid])
        else:
            q.message.reply_text("❌ No Thumbnail Saved")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, m):
    uid = m.from_user.id
    mode = user_mode.get(uid)

    if mode == "wait_file":
        user_file[uid] = m
        m.reply_text("Choose Rename Mode", reply_markup=rename_menu())

    elif mode == "f2v":
        queue.put((m, "convert", uid, "f2v"))

# ===== TEXT HANDLER =====
@app.on_message(filters.text & ~filters.command("start"))
def text_handler(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) == "manual":
        queue.put((user_file.get(uid), m.text, uid, "rename"))

    elif user_mode.get(uid) == "setname":
        saved_name[uid] = m.text
        m.reply_text("✅ Saved")

# ===== PHOTO (THUMB SAVE) =====
@app.on_message(filters.photo)
def photo_handler(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) == "setthumb":
        path = m.download(f"{THUMB}/{uid}.jpg")
        user_saved_thumb[uid] = path
        user_mode[uid] = None
        m.reply_text("✅ Thumbnail Saved")

# ===== WORKER =====
def worker():
    while True:
        file, name, uid, mode = queue.get()
        try:
            process(file, name, uid, mode)
        except Exception as e:
            file.reply_text(f"❌ Error: {e}")
        queue.task_done()

# ===== PROCESS =====
def process(file, name, uid, mode):

    msg = file.reply_text("⏳ Starting...", reply_markup=progress_btn())
    start = time.time()

    def dprog(c, t):
        p = int(c*100/t)
        speed = c/(time.time()-start+1)
        eta = (t-c)/(speed+1)

        msg.edit_text(
            f"⬇ Downloading\n[{progress_bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n⏱ ETA {int(eta)}s",
            reply_markup=progress_btn()
        )

    path = file.download(file_name=f"{DOWNLOAD}/{time.time()}", progress=dprog)

    msg.edit_text("⚙ Processing...", reply_markup=progress_btn())

    # ===== CONVERT =====
    if mode == "f2v":
        out = f"{OUTPUT}/{time.time()}.mp4"
        subprocess.run(["ffmpeg","-i",path,"-c:v","libx264","-preset","ultrafast","-c:a","aac",out])
        path = out

    # ===== THUMB =====
    thumb = None
    if user_thumb_mode.get(uid) == "saved":
        thumb = user_saved_thumb.get(uid)
    elif user_thumb_mode.get(uid) == "auto":
        thumb = f"{THUMB}/{time.time()}.jpg"
        subprocess.run(["ffmpeg","-i",path,"-ss","2","-vframes","1",thumb])

    msg.edit_text("⬆ Uploading...", reply_markup=progress_btn())

    def uprog(c, t):
        p = int(c*100/t)
        msg.edit_text(
            f"⬆ Uploading\n[{progress_bar(p)}] {p}%",
            reply_markup=progress_btn()
        )

    ext = os.path.splitext(path)[1]

    if ext == ".mp4":
        file.reply_video(path, caption=f"✅ {name}", thumb=thumb, supports_streaming=True, progress=uprog)
    else:
        file.reply_document(path, caption=f"✅ {name}", progress=uprog)

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 Bot Running...")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
