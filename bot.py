# ===== GOD LEVEL TELEGRAM BOT =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserNotParticipant
from config import *
import os, re, time, threading, json
from queue import Queue
from flask import Flask

# ===== SETTINGS =====
CHANNEL = "Anitoon_edit"
CHANNEL_LINK = "https://t.me/Anitoon_edit"
CHANNEL_POST = "https://t.me/Anitoon_edit/33"
WORKERS = 3

# ===== STORAGE =====
if not os.path.exists("thumbs"):
    os.mkdir("thumbs")

if not os.path.exists("db.json"):
    with open("db.json", "w") as f:
        json.dump({}, f)

# ===== FLASK =====
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot Running ✅"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# ===== BOT =====
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== DATA =====
task_queue = Queue()
user_files = {}
user_steps = {}
active_tasks = 0

# ===== DB =====
def load_db():
    return json.load(open("db.json"))

def save_db(data):
    json.dump(data, open("db.json", "w"))

def get_user(uid):
    db = load_db()
    return db.get(str(uid), {})

def update_user(uid, key, value):
    db = load_db()
    if str(uid) not in db:
        db[str(uid)] = {}
    db[str(uid)][key] = value
    save_db(db)

# ===== JOIN CHECK =====
def is_joined(client, uid):
    try:
        client.get_chat_member(CHANNEL, uid)
        return True
    except UserNotParticipant:
        return False
    except:
        return True

# ===== RENAME =====
def smart_name(name):
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+', '', name)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'\b(720p|1080p|4k|HDRip|BluRay|x264|x265)\b', '', name, flags=re.I)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip().title() or "AniToon_File"

# ===== UI =====
def bar(p):
    return "█"*int(p/10) + "░"*(10-int(p/10))

def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 AniToon's Channel", url=CHANNEL_LINK)]
    ])

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel List", url=CHANNEL_POST)]
    ])

def safe_edit(m, t, b=None):
    try:
        m.edit_text(t, reply_markup=b)
    except:
        pass

# ===== MENUS =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Rename", callback_data="rename")],
        [InlineKeyboardButton("🎬 Video Tools", callback_data="video")],
        [InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

def video_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞 File → Video", callback_data="f2v")],
        [InlineKeyboardButton("📂 Video → File", callback_data="v2f")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(c, m):

    if not is_joined(c, m.from_user.id):
        m.reply_text("🚫 Join first", reply_markup=join_btn())
        return

    m.reply_text("🔥 GOD LEVEL BOT", reply_markup=main_menu())

# ===== BUTTONS =====
@app.on_callback_query()
def buttons(c, q):

    uid = q.from_user.id
    d = q.data

    if not is_joined(c, uid):
        safe_edit(q.message, "🚫 Join first", join_btn())
        return

    if d == "rename":
        safe_edit(q.message, "📁 Send file")

    elif d == "video":
        safe_edit(q.message, "🎬 Tools", video_menu())

    elif d == "thumb":
        user_steps[uid] = "thumb"
        safe_edit(q.message, "🖼 Send thumbnail")

    elif d == "status":
        safe_edit(q.message, f"📊 Queue: {task_queue.qsize()}\n⚡ Active: {active_tasks}")

    elif d == "back":
        safe_edit(q.message, "🏠 Menu", main_menu())

    elif d == "auto":
        file = user_files.get(uid)
        if not file:
            return

        name = file.document.file_name
        new = smart_name(os.path.splitext(name)[0])

        pos = task_queue.qsize()+1
        task_queue.put((file, new, q.message))
        safe_edit(q.message, f"⏳ Queue: {pos}")

# ===== FILE =====
@app.on_message(filters.document | filters.video | filters.audio)
def file(c, m):

    if not is_joined(c, m.from_user.id):
        m.reply_text("🚫 Join first", reply_markup=join_btn())
        return

    uid = m.from_user.id
    user_files[uid] = m

    name = m.document.file_name if m.document else "file"
    sug = smart_name(os.path.splitext(name)[0])

    m.reply_text(f"💡 `{sug}`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Auto", callback_data="auto")]
        ])
    )

# ===== THUMB =====
@app.on_message(filters.photo)
def thumb(c, m):

    uid = m.from_user.id
    if user_steps.get(uid) != "thumb":
        return

    path = m.download(f"thumbs/{uid}.jpg")
    update_user(uid, "thumb", path)

    user_steps.pop(uid)
    m.reply_text("✅ Thumbnail saved")

# ===== WORKER =====
def worker():
    global active_tasks

    while True:
        f, name, msg = task_queue.get()
        active_tasks += 1

        try:
            process(f, name, msg)
        except Exception as e:
            msg.reply_text(f"❌ {e}")

        active_tasks -= 1
        task_queue.task_done()

# ===== PROCESS =====
def process(f, name, msg):

    uid = f.from_user.id
    thumb = get_user(uid).get("thumb")

    pmsg = msg.reply_text("⏳ Starting...", reply_markup=progress_btn())

    last = -5
    start = time.time()

    def prog(c, t):
        nonlocal last
        p = int(c*100/t)
        if p-last < 5:
            return
        last = p

        safe_edit(pmsg, f"📥 [{bar(p)}] {p}%", progress_btn())

    path = f.download(progress=prog)

    ext = os.path.splitext(path)[1]
    new = f"{name}{ext}"
    os.rename(path, new)

    f.reply_document(new, caption=f"✅ {name}", thumb=thumb if thumb else None)

    try:
        pmsg.delete()
    except:
        pass

    os.remove(new)

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 GOD BOT START")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
