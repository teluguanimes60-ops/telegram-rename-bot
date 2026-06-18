# ===== AniToons Rename Bot (ULTRA PRO MAX EXTENDED) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, subprocess
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
CHANNEL_POST = "https://t.me/Anitoon_edit/33"
WORKERS = 5   # increased
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

# ===== FOLDERS =====
os.makedirs("thumbs", exist_ok=True)
os.makedirs("downloads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

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
    workers=100
)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_mode = {}
active_tasks = 0

# ===== SMART RENAME (UPGRADED) =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+', '', name)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    quality = re.findall(r'(480p|720p|1080p|4k)', name, re.I)
    quality = quality[0] if quality else ""

    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    return f"{name.title()} {quality.upper()}".strip() or "AniToon_File"

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
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

def rename_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Auto Rename", callback_data="auto")],
        [InlineKeyboardButton("✏ Manual Rename", callback_data="manual")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Media Info", callback_data="info")],
        [InlineKeyboardButton("🎞 Convert → MP4", callback_data="f2v")],
        [InlineKeyboardButton("📂 Convert → MKV", callback_data="v2f")],
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
        "🔥 **AniToons Rename Bot PRO**\n\n"
        "⚡ Ultra Fast System\n"
        "🎬 Video Converter Enabled\n"
        "📦 Smart Rename Engine\n\n"
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
        q.message.edit_text("📁 Send file to rename", reply_markup=rename_menu())

    elif data == "video":
        user_mode[uid] = "video"
        q.message.edit_text("🎬 Send file/video", reply_markup=video_menu())

    elif data == "settings":
        q.message.edit_text("⚙ Send thumbnail image", reply_markup=settings_menu())

    elif data == "manual":
        user_mode[uid] = "manual"
        q.message.edit_text("✏ Send new filename")

    elif data == "thumb":
        user_mode[uid] = "thumb"
        q.message.edit_text("🖼 Send thumbnail image")

    elif data == "auto":
        file = user_files.get(uid)
        if file:
            name = file.document.file_name if file.document else "file"
            task_queue.put((file, smart_name(name)))

    elif data == "info":
        user_mode[uid] = "info"
        q.message.edit_text("📊 Send media")

    elif data == "f2v":
        user_mode[uid] = "f2v"
        q.message.edit_text("🎞 Send file")

    elif data == "v2f":
        user_mode[uid] = "v2f"
        q.message.edit_text("📂 Send video")

    elif data == "back":
        user_mode[uid] = None
        q.message.edit_text("🏠 Menu", reply_markup=main_menu())

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, msg):

    uid = msg.from_user.id
    mode = user_mode.get(uid)

    if msg.document and msg.document.file_size > MAX_FILE_SIZE:
        msg.reply_text("❌ File too large")
        return

    # INFO
    if mode == "info":
        f = msg.video or msg.document or msg.audio
        msg.reply_text(
            f"📦 Size: {round(f.file_size/1024/1024,2)} MB\n"
            f"🎬 Type: {type(f).__name__}"
        )
        return

    # CONVERSION
    if mode in ["f2v", "v2f"]:
        task_queue.put((msg, "converted"))
        return

    # RENAME
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

# ===== PROCESS (HEAVY UPGRADE) =====
def process(file, name):

    uid = file.from_user.id
    mode = user_mode.get(uid)

    pmsg = file.reply_text("🚀 Processing...", reply_markup=progress_btn())
    start = time.time()

    def progress(c, t):
        p = int(c*100/t)
        speed = c/(time.time()-start+1)

        pmsg.edit_text(
            f"🚀 Processing\n[{bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n🔥 Ultra Mode",
            reply_markup=progress_btn()
        )

    path = file.download(file_name=f"downloads/{time.time()}", progress=progress)

    # CONVERT
    if mode == "f2v":
        out = f"outputs/{time.time()}.mp4"
        subprocess.run(["ffmpeg","-i",path,out])
        path = out

    elif mode == "v2f":
        out = f"outputs/{time.time()}.mkv"
        subprocess.run(["ffmpeg","-i",path,"-c","copy",out])
        path = out

    ext = os.path.splitext(path)[1]
    new_file = f"outputs/{name}{ext}"
    os.rename(path, new_file)

    # SEND FIX
    if ext in [".mp4", ".mkv"]:
        file.reply_video(new_file, caption=f"✅ {name}")
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
