# ===== GOD+++++ FINAL ULTIMATE TELEGRAM BOT =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, json
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
    web.run(host="0.0.0.0", port=10000)

# ===== BOT =====
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_steps = {}
active_tasks = 0

# ===== SMART RENAME =====
def smart_name(name):

    name = re.sub(r'@\w+', '', name)

    season = re.findall(r'(S\d{1,2}|Season ?\d+)', name, re.I)
    episode = re.findall(r'(E\d{1,3}|Ep ?\d+)', name, re.I)
    quality = re.findall(r'(480p|720p|1080p|2160p|4k)', name, re.I)

    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    base = name.strip().title()

    extra = " ".join(season + episode + quality)

    final = f"{base} {extra}".strip()

    return final if final else "AniToon_File"

# ===== UI =====
def bar(p):
    return "█" * int(p/10) + "░" * (10-int(p/10))

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 AniToon's List", url=CHANNEL_POST)]
    ])

def safe_edit(msg, text, btn=None):
    try:
        msg.edit_text(text, reply_markup=btn)
    except:
        pass

# ===== MENUS =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename")],
        [InlineKeyboardButton("🎬 Video Tools", callback_data="video")],
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")]
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
        btns.append([InlineKeyboardButton("➕ Add Saved Name", callback_data="add_saved")])

    return InlineKeyboardMarkup(btns)

def settings_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Set Saved Name", callback_data="setname")],
        [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("🗑 Remove Thumbnail", callback_data="delthumb")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 File → Video", callback_data="f2v")],
        [InlineKeyboardButton("📂 Video → File", callback_data="v2f")],
        [InlineKeyboardButton("📊 Media Info", callback_data="info")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(client, msg):
    msg.reply_text("🔥 AniToon GOD+++++ BOT\n\nUltimate Features Enabled 🚀", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(client, q):

    uid = q.from_user.id
    data = q.data

    if data == "rename":
        safe_edit(q.message, "📁 Send file to rename", rename_menu(uid))

    elif data == "video":
        safe_edit(q.message, "🎬 Video Tools", video_menu())

    elif data == "settings":
        safe_edit(q.message, "⚙ Settings Panel", settings_menu(uid))

    elif data == "status":
        safe_edit(q.message, f"📊 Queue: {task_queue.qsize()}\n⚡ Active: {active_tasks}")

    elif data == "back":
        safe_edit(q.message, "🏠 Main Menu", main_menu())

    elif data == "manual":
        user_steps[uid] = "rename"
        safe_edit(q.message, "✏ Send new name")

    elif data == "setname":
        user_steps[uid] = "setname"
        safe_edit(q.message, "📌 Send name to save")

    elif data == "saved":
        file = user_files.get(uid)
        if not file:
            return
        saved = get_user(uid).get("saved_name")
        task_queue.put((file, saved, q.message))
        safe_edit(q.message, "⏳ Using saved name...")

    elif data == "auto":
        file = user_files.get(uid)
        if not file:
            return
        name = file.document.file_name if file.document else "file"
        new = smart_name(os.path.splitext(name)[0])
        task_queue.put((file, new, q.message))
        safe_edit(q.message, "⚡ Auto Rename Started")

    elif data == "delthumb":
        set_user(uid, "thumb", None)
        safe_edit(q.message, "🗑 Thumbnail removed")

    elif data == "info":
        user_steps[uid] = "info"
        safe_edit(q.message, "📊 Send file to get info")

# ===== FILE =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(client, msg):

    uid = msg.from_user.id
    user_files[uid] = msg

    name = msg.document.file_name if msg.document else "file"
    sug = smart_name(os.path.splitext(name)[0])

    msg.reply_text(f"💡 Suggested:\n`{sug}`", reply_markup=rename_menu(uid))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text_handler(client, msg):

    uid = msg.from_user.id

    if user_steps.get(uid) == "rename":
        file = user_files.get(uid)
        task_queue.put((file, msg.text.strip(), msg))
        msg.reply_text("⏳ Added to queue")

    elif user_steps.get(uid) == "setname":
        set_user(uid, "saved_name", msg.text.strip())
        msg.reply_text("✅ Saved name updated")

# ===== THUMB =====
@app.on_message(filters.photo)
def thumb(client, msg):

    uid = msg.from_user.id
    path = msg.download(f"thumbs/{uid}.jpg")
    set_user(uid, "thumb", path)
    msg.reply_text("✅ Thumbnail saved")

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

    pmsg = msg.reply_text("⏳ Starting...", reply_markup=progress_btn())

    last = -1
    start = time.time()

    def progress(c, t):
        nonlocal last
        p = int(c*100/t)

        if p == last:
            return
        last = p

        speed = c / (time.time() - start + 1)
        eta = (t - c) / (speed + 1)

        safe_edit(
            pmsg,
            f"📥 Downloading...\n\n[{bar(p)}] {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n⏳ {int(eta)} sec",
            progress_btn()
        )

    path = file.download(progress=progress)

    ext = os.path.splitext(path)[1]
    new_file = f"{name}{ext}"
    os.rename(path, new_file)

    def upload(c, t):
        p = int(c*100/t)
        safe_edit(
            pmsg,
            f"📤 Uploading...\n\n[{bar(p)}] {p}%",
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
            print("🚀 GOD+++++ BOT START")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
