# ===== ULTIMATE GOD++ TELEGRAM BOT (UPDATED) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import *
import os, re, time, threading, json
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
WORKERS = 3
CHANNEL_POST = "https://t.me/Anitoon_edit/33"

# ===== FILE SYSTEM =====
if not os.path.exists("thumbs"):
    os.mkdir("thumbs")

DB_FILE = "db.json"
if not os.path.exists(DB_FILE):
    json.dump({}, open(DB_FILE, "w"))

# ===== DATABASE =====
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

# ===== SMART RENAME (KEEP S/E/QUALITY) =====
def smart_name(name):

    # remove @ tags only
    name = re.sub(r'@\w+', '', name)

    # remove brackets
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    # KEEP season/episode/quality
    # only clean symbols
    name = re.sub(r'[._\-]', ' ', name)

    # remove extra spaces
    name = re.sub(r'\s+', ' ', name)

    return name.strip().title() or "AniToon_File"

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
        [InlineKeyboardButton("🎬 Video Settings", callback_data="video_settings")],
        [InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_menu")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

def rename_menu(uid):
    user = get_user(uid)
    saved = user.get("saved_name")

    buttons = [
        [
            InlineKeyboardButton("⚡ Auto", callback_data="auto"),
            InlineKeyboardButton("✏ Manual", callback_data="manual")
        ]
    ]

    if saved:
        buttons.append([InlineKeyboardButton("📌 Use Saved Name", callback_data="saved")])
    else:
        buttons.append([InlineKeyboardButton("➕ Save Name", callback_data="add_saved")])

    return InlineKeyboardMarkup(buttons)

def settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Save Rename Name", callback_data="add_saved")],
        [InlineKeyboardButton("✏ Change Saved Name", callback_data="change_saved")],
        [InlineKeyboardButton("🖼 Thumbnail Settings", callback_data="thumb_settings")]
    ])

def thumb_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Thumbnail", callback_data="add_thumb")],
        [InlineKeyboardButton("🔁 Change Thumbnail", callback_data="add_thumb")],
        [InlineKeyboardButton("⚙ Thumbnail Mode", callback_data="thumb_settings")]
    ])

def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 File → Video", callback_data="f2v")],
        [InlineKeyboardButton("📂 Video → File", callback_data="v2f")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(_, msg):
    msg.reply_text("🔥 ULTIMATE BOT\n\nChoose option:", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(_, q):

    uid = q.from_user.id
    data = q.data

    if data == "rename":
        safe_edit(q.message, "📁 Send file to rename")

    elif data == "video_settings":
        safe_edit(q.message, "🎬 Choose conversion type", video_menu())

    elif data == "thumb_menu":
        safe_edit(q.message, "🖼 Thumbnail options", thumb_menu(uid))

    elif data == "settings":
        safe_edit(q.message, "⚙ Settings Panel", settings_menu())

    elif data == "status":
        safe_edit(q.message, f"📊 Queue: {task_queue.qsize()}\n⚡ Active: {active_tasks}")

    elif data == "manual":
        user_steps[uid] = "rename"
        safe_edit(q.message, "✏ Send custom name")

    elif data == "add_saved":
        user_steps[uid] = "save_name"
        safe_edit(q.message, "➕ Send name to save")

    elif data == "change_saved":
        user_steps[uid] = "save_name"
        safe_edit(q.message, "✏ Send new saved name")

    elif data == "saved":
        file = user_files.get(uid)
        saved = get_user(uid).get("saved_name")

        if not file or not saved:
            safe_edit(q.message, "❌ No saved name")
            return

        task_queue.put((file, saved, q.message))
        safe_edit(q.message, "⏳ Using saved name...")

    elif data == "auto":
        file = user_files.get(uid)
        if not file:
            return

        name = file.document.file_name if file.document else "file"
        new = smart_name(os.path.splitext(name)[0])

        task_queue.put((file, new, q.message))
        safe_edit(q.message, "⏳ Auto rename started")

    elif data == "add_thumb":
        user_steps[uid] = "thumb"
        safe_edit(q.message, "🖼 Send thumbnail image")

# ===== FILE =====
@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, msg):

    uid = msg.from_user.id
    user_files[uid] = msg

    name = msg.document.file_name if msg.document else "file"
    sug = smart_name(os.path.splitext(name)[0])

    msg.reply_text(
        f"💡 Suggested:\n`{sug}`",
        reply_markup=rename_menu(uid)
    )

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text_handler(_, msg):

    uid = msg.from_user.id

    if user_steps.get(uid) == "rename":
        file = user_files.get(uid)
        if not file:
            return

        task_queue.put((file, msg.text.strip(), msg))
        msg.reply_text("⏳ Added")

    elif user_steps.get(uid) == "save_name":
        set_user(uid, "saved_name", msg.text.strip())
        user_steps.pop(uid)
        msg.reply_text("✅ Name saved")

# ===== THUMB =====
@app.on_message(filters.photo)
def save_thumb(_, msg):

    uid = msg.from_user.id
    if user_steps.get(uid) != "thumb":
        return

    path = msg.download(f"thumbs/{uid}.jpg")
    set_user(uid, "thumb", path)

    user_steps.pop(uid)
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
        safe_edit(pmsg, f"📤 Uploading...\n\n[{bar(p)}] {p}%", progress_btn())

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
            print("🚀 BOT STARTED")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
