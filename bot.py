# ===== AniToons Rename Bot (ULTRA PRO MAX GOD VERSION 🚀) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, subprocess, shutil
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
os.makedirs("screenshots", exist_ok=True)
os.makedirs("zips", exist_ok=True)

# ===== FLASK =====
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

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
user_files = {}
user_mode = {}
active_tasks = 0

# ===== ADVANCED SMART NAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+', '', name)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    season = re.findall(r'(S\d{1,2}|Season ?\d+)', name, re.I)
    episode = re.findall(r'(E\d{1,3}|Ep ?\d+)', name, re.I)
    quality = re.findall(r'(480p|720p|1080p|4k)', name, re.I)

    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    extra = " ".join(season + episode + quality)
    return f"{name.title()} {extra}".strip() or "AniToon_File"

# ===== UI =====
def bar(p):
    return "█"*int(p/10) + "░"*(10-int(p/10))

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url=CHANNEL_POST)],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename Files", callback_data="rename")],
        [InlineKeyboardButton("🎬 Video Tools", callback_data="video")],
        [InlineKeyboardButton("🧠 AI Rename", callback_data="ai")],
        [InlineKeyboardButton("📦 Zip Tools", callback_data="zip")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):
    msg.reply_text(
        "🔥 **AniToons ULTRA BOT**\n\n"
        "⚡ Netflix Style Rename\n"
        "🎬 Video Tools + Screenshots\n"
        "📦 Zip + Batch Rename\n"
        "🚀 Ultra Speed Engine (3MB/s+)\n\n"
        "👇 Select Option",
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
        q.message.edit_text("📁 Send files", reply_markup=main_menu())

    elif data == "video":
        user_mode[uid] = "video"
        q.message.edit_text("🎬 Send video for tools")

    elif data == "ai":
        user_mode[uid] = "ai"
        q.message.edit_text("🧠 AI Rename Mode Enabled\nSend file")

    elif data == "zip":
        user_mode[uid] = "zip"
        q.message.edit_text("📦 Send multiple files to zip")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, msg):

    uid = msg.from_user.id
    mode = user_mode.get(uid)

    if msg.document and msg.document.file_size > MAX_FILE_SIZE:
        msg.reply_text("❌ File too large")
        return

    if mode == "ai":
        name = smart_name(msg.document.file_name if msg.document else "file")
        task_queue.put((msg, name))
        return

    if mode == "zip":
        folder = f"zips/{uid}"
        os.makedirs(folder, exist_ok=True)
        path = msg.download(file_name=f"{folder}/{time.time()}")
        msg.reply_text("📦 Added to zip queue")
        return

    user_files[uid] = msg
    name = msg.document.file_name if msg.document else "file"
    sug = smart_name(name)

    msg.reply_text(f"✨ Suggested:\n`{sug}`")

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

# ===== PROCESS =====
def process(file, name):

    uid = file.from_user.id
    pmsg = file.reply_text("🚀 Ultra Processing...", reply_markup=progress_btn())
    start = time.time()

    def progress(c, t):
        p = int(c*100/t)
        speed = c/(time.time()-start+1)

        pmsg.edit_text(
            f"🚀 Processing\n[{bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n🔥 Turbo Mode",
            reply_markup=progress_btn()
        )

    path = file.download(file_name=f"downloads/{time.time()}", progress=progress)

    # ===== AUTO THUMB FROM VIDEO =====
    thumb = None
    if path.endswith(".mp4"):
        thumb = f"screenshots/{time.time()}.jpg"
        subprocess.run(["ffmpeg", "-i", path, "-ss", "00:00:05", "-vframes", "1", thumb])

    # ===== SCREENSHOTS =====
    if path.endswith(".mp4"):
        for i in range(3):
            subprocess.run([
                "ffmpeg", "-i", path,
                "-ss", f"00:00:0{i+2}",
                "-vframes", "1",
                f"screenshots/{uid}_{i}.jpg"
            ])

    ext = os.path.splitext(path)[1]
    new_file = f"outputs/{name}{ext}"
    os.rename(path, new_file)

    # ===== SEND =====
    if ext in [".mp4", ".mkv"]:
        file.reply_video(
            new_file,
            caption=f"✅ {name}",
            thumb=thumb if thumb and os.path.exists(thumb) else None
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
            print("🚀 BOT STARTED ULTRA MODE")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
