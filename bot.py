# ===== AniToons Rename Bot (ULTRA PRO MAX FINAL) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, json, subprocess
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
CHANNEL_POST = "https://t.me/Anitoon_edit/33"
WORKERS = 4   # increased workers for speed

# ===== FOLDERS =====
os.makedirs("thumbs", exist_ok=True)

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
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

# ===== BOT =====
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50   # HIGH SPEED INTERNAL THREADS
)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_mode = {}
active_tasks = 0

# ===== SMART RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)

    season = re.findall(r'(S\d{1,2}|Season ?\d+)', name, re.I)
    episode = re.findall(r'(E\d{1,3}|Ep ?\d+)', name, re.I)
    quality = re.findall(r'(480p|720p|1080p|4k)', name, re.I)

    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    base = name.strip().title()
    extra = " ".join(season + episode + quality)

    return f"{base} {extra}".strip() or "AniToon_File"

# ===== UI =====
def bar(p):
    return "█"*int(p/10) + "░"*(10-int(p/10))

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Updates", url=CHANNEL_POST)],
        [InlineKeyboardButton("❌ Cancel Task", callback_data="cancel")]
    ])

def safe_edit(msg, text, btn=None):
    try:
        msg.edit_text(text, reply_markup=btn)
    except:
        pass

# ===== MENUS =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename Files", callback_data="rename")],
        [InlineKeyboardButton("🎬 Video Tools", callback_data="video")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Bot Status", callback_data="status")]
    ])

def rename_menu(uid):
    saved = get_user(uid).get("saved_name")

    btns = [
        [InlineKeyboardButton("⚡ Auto Rename", callback_data="auto")],
        [InlineKeyboardButton("✏ Manual Rename", callback_data="manual")]
    ]

    if saved:
        btns.append([InlineKeyboardButton("📌 Use Saved Name", callback_data="saved")])
    else:
        btns.append([InlineKeyboardButton("➕ Save Name", callback_data="setname")])

    btns.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(btns)

def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Media Info", callback_data="info")],
        [InlineKeyboardButton("🎞 Convert to Video", callback_data="f2v")],
        [InlineKeyboardButton("📂 Convert to File", callback_data="v2f")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def settings_menu(uid):
    thumb = get_user(uid).get("thumb")

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Save Name", callback_data="setname")],
        [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("👁 View Thumbnail", callback_data="view_thumb")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):
    msg.reply_text(
        "🔥 **AniToons Rename Bot**\n\n"
        "⚡ Ultra Fast Rename + Video Tools\n"
        "🚀 High Speed Processing Engine\n\n"
        "👇 Choose what you want to do:",
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
        safe_edit(q.message, "📁 Send file to rename", rename_menu(uid))

    elif data == "video":
        user_mode[uid] = "video"
        safe_edit(q.message, "🎬 Send file/video", video_menu())

    elif data == "settings":
        safe_edit(q.message, "⚙ Settings Panel", settings_menu(uid))

    elif data == "view_thumb":
        thumb = get_user(uid).get("thumb")
        if thumb and os.path.exists(thumb):
            client.send_photo(uid, thumb, caption="🖼 Your Thumbnail")
        else:
            q.message.reply_text("❌ No thumbnail set")

    elif data == "status":
        safe_edit(q.message, f"📊 Queue: {task_queue.qsize()}\n⚡ Active: {active_tasks}")

    elif data == "back":
        user_mode[uid] = None
        safe_edit(q.message, "🏠 Main Menu", main_menu())

    elif data == "manual":
        user_mode[uid] = "manual"
        safe_edit(q.message, "✏ Send new name")

    elif data == "setname":
        user_mode[uid] = "setname"
        safe_edit(q.message, "📌 Send name")

    elif data == "thumb":
        user_mode[uid] = "thumb"
        safe_edit(q.message, "🖼 Send thumbnail image")

    elif data == "auto":
        file = user_files.get(uid)
        if file:
            name = file.document.file_name if file.document else "file"
            new = smart_name(os.path.splitext(name)[0])
            task_queue.put((file, new, q.message))

    elif data == "saved":
        file = user_files.get(uid)
        saved = get_user(uid).get("saved_name")
        if file and saved:
            task_queue.put((file, saved, q.message))

    elif data == "info":
        user_mode[uid] = "info"
        safe_edit(q.message, "📊 Send media")

    elif data == "f2v":
        user_mode[uid] = "f2v"
        safe_edit(q.message, "🎞 Send file")

    elif data == "v2f":
        user_mode[uid] = "v2f"
        safe_edit(q.message, "📂 Send video")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, msg):

    uid = msg.from_user.id
    mode = user_mode.get(uid)

    if mode == "info":
        f = msg.video or msg.document or msg.audio
        msg.reply_text(f"📦 Size: {round(f.file_size/1024/1024,2)} MB")
        return

    if mode in ["f2v", "v2f"]:
        task_queue.put((msg, "converted", msg))
        return

    user_files[uid] = msg

    name = msg.document.file_name if msg.document else "file"
    sug = smart_name(os.path.splitext(name)[0])

    msg.reply_text(f"✨ Suggested:\n`{sug}`", reply_markup=rename_menu(uid))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text_handler(client, msg):

    uid = msg.from_user.id

    if user_mode.get(uid) == "manual":
        file = user_files.get(uid)
        if file:
            task_queue.put((file, msg.text.strip(), msg))

    elif user_mode.get(uid) == "setname":
        set_user(uid, "saved_name", msg.text.strip())
        msg.reply_text("✅ Saved")

# ===== THUMB =====
@app.on_message(filters.photo)
def thumb(client, msg):

    uid = msg.from_user.id

    if user_mode.get(uid) != "thumb":
        return

    path = msg.download(f"thumbs/{uid}.jpg")
    set_user(uid, "thumb", path)

    user_mode[uid] = None
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
    mode = user_mode.get(uid)

    pmsg = msg.reply_text("🚀 Processing...", reply_markup=progress_btn())
    start = time.time()

    def progress(c, t):
        p = int(c*100/t)
        speed = c/(time.time()-start+1)

        safe_edit(
            pmsg,
            f"🚀 Processing\n[{bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n🔥 Ultra Speed",
            progress_btn()
        )

    path = file.download(progress=progress)

    # ===== CONVERT =====
    if mode == "f2v":
        new_path = "out.mp4"
        subprocess.run(["ffmpeg","-i",path,new_path])
        path = new_path

    elif mode == "v2f":
        new_path = "out.mkv"
        subprocess.run(["ffmpeg","-i",path,"-c","copy",new_path])
        path = new_path

    ext = os.path.splitext(path)[1]
    new_file = f"{name}{ext}"
    os.rename(path, new_file)

    # ===== FIX: VIDEO SEND =====
    if ext in [".mp4", ".mkv"]:
        file.reply_video(new_file, caption=f"✅ {name}", thumb=thumb if thumb else None)
    else:
        file.reply_document(new_file, caption=f"✅ {name}", thumb=thumb if thumb else None)

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
