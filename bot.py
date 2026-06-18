# ===== AniToons Rename Bot (ULTRA PRO MAX FINAL UPGRADED) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, subprocess
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
CHANNEL_POST = "https://t.me/Anitoon_edit/33"
WORKERS = 6
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

# ===== FOLDERS =====
os.makedirs("thumbs", exist_ok=True)
os.makedirs("downloads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# ===== WEB KEEP ALIVE =====
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
    workers=120
)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_mode = {}
active_tasks = 0

# ===== SMART RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+', '', name)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    quality = re.findall(r'(480p|720p|1080p|2160p|4k)', name, re.I)
    quality = quality[0].upper() if quality else ""

    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    return f"{name.title()} {quality}".strip() or "AniToon_File"

# ===== UI =====
def bar(p):
    return "█"*int(p/10) + "░"*(10-int(p/10))

def progress_text(p, speed):
    return (
        f"🚀 Processing File...\n\n"
        f"[{bar(p)}] {p}%\n\n"
        f"⚡ Speed: {round(speed/1024/1024,2)} MB/s\n"
        f"🔥 High Speed Mode Enabled"
    )

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url=CHANNEL_POST)],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename File", callback_data="rename")],
        [InlineKeyboardButton("🎬 Convert Video/File", callback_data="convert")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

def rename_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Auto Rename", callback_data="auto")],
        [InlineKeyboardButton("✏ Manual Rename", callback_data="manual")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def convert_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 File → Video", callback_data="f2v")],
        [InlineKeyboardButton("📂 Video → File", callback_data="v2f")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):
    msg.reply_text(
        "🔥 **AniToons Bot**\n\n"
        "⚡ Fast Rename\n"
        "🎬 Convert File ↔ Video\n"
        "🖼 Auto Thumbnail System\n\n"
        "👇 Choose option:",
        reply_markup=main_menu()
    )

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(client, q):
    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "rename":
        user_mode[uid] = "rename"
        q.message.edit_text("📁 Send file", reply_markup=rename_menu())

    elif data == "convert":
        user_mode[uid] = "convert"
        q.message.edit_text("🎬 Choose conversion", reply_markup=convert_menu())

    elif data == "settings":
        q.message.edit_text("⚙ Send thumbnail image", reply_markup=settings_menu())

    elif data == "manual":
        user_mode[uid] = "manual"
        q.message.edit_text("✏ Send new filename")

    elif data == "auto":
        file = user_files.get(uid)
        if file:
            name = file.document.file_name if file.document else "file"
            task_queue.put((file, smart_name(name)))

    elif data == "f2v":
        user_mode[uid] = "f2v"
        q.message.edit_text("🎞 Send file")

    elif data == "v2f":
        user_mode[uid] = "v2f"
        q.message.edit_text("📂 Send video")

    elif data == "thumb":
        user_mode[uid] = "thumb"
        q.message.edit_text("🖼 Send image")

    elif data == "back":
        user_mode[uid] = None
        q.message.edit_text("🏠 Menu", reply_markup=main_menu())

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video)
def file_handler(client, msg):

    uid = msg.from_user.id
    mode = user_mode.get(uid)

    if msg.document and msg.document.file_size > MAX_FILE_SIZE:
        msg.reply_text("❌ File too large")
        return

    if mode in ["f2v", "v2f"]:
        task_queue.put((msg, "converted"))
        return

    user_files[uid] = msg

    name = msg.document.file_name if msg.document else "file"
    sug = smart_name(name)

    msg.reply_text(f"✨ Suggested:\n`{sug}`", reply_markup=rename_menu())

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text_handler(client, msg):
    uid = msg.from_user.id

    if user_mode.get(uid) == "manual":
        file = user_files.get(uid)
        if file:
            task_queue.put((file, msg.text.strip()))

# ===== THUMB =====
@app.on_message(filters.photo)
def thumb(client, msg):
    uid = msg.from_user.id

    if user_mode.get(uid) != "thumb":
        return

    path = msg.download(f"thumbs/{uid}.jpg")
    user_mode[uid] = None
    msg.reply_text("✅ Thumbnail Saved")

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

# ===== AUTO THUMB FROM VIDEO =====
def generate_thumb(video_path, uid):
    thumb_path = f"thumbs/{uid}_auto.jpg"
    try:
        subprocess.run([
            "ffmpeg", "-i", video_path,
            "-ss", "00:00:02",
            "-vframes", "1",
            thumb_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return thumb_path if os.path.exists(thumb_path) else None
    except:
        return None

# ===== PROCESS =====
def process(file, name):

    uid = file.from_user.id
    mode = user_mode.get(uid)

    pmsg = file.reply_text("🚀 Processing...", reply_markup=progress_btn())
    start = time.time()

    def progress(c, t):
        p = int(c*100/t)
        speed = c/(time.time()-start+1)
        try:
            pmsg.edit_text(progress_text(p, speed), reply_markup=progress_btn())
        except:
            pass

    path = file.download(file_name=f"downloads/{time.time()}", progress=progress)

    # ===== CONVERT =====
    if mode == "f2v":
        out = f"outputs/{time.time()}.mp4"
        subprocess.run(["ffmpeg", "-i", path, "-c:v", "libx264", "-preset", "ultrafast", out])
        path = out

    elif mode == "v2f":
        out = f"outputs/{time.time()}.mkv"
        subprocess.run(["ffmpeg", "-i", path, "-c", "copy", out])
        path = out

    ext = os.path.splitext(path)[1]
    new_file = f"outputs/{name}{ext}"
    os.rename(path, new_file)

    # ===== THUMB =====
    thumb = f"thumbs/{uid}.jpg"
    if not os.path.exists(thumb) and ext in [".mp4", ".mkv"]:
        thumb = generate_thumb(new_file, uid)

    # ===== SEND =====
    if ext in [".mp4", ".mkv"]:
        file.reply_video(
            new_file,
            caption=f"✅ {name}",
            thumb=thumb if thumb else None,
            supports_streaming=True
        )
    else:
        file.reply_document(new_file, caption=f"✅ {name}")

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
