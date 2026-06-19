# ===== AniToons Rename Bot (ULTRA VERSION) =====

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

# ===== WEB =====
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ===== BOT =====
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== DATA =====
queue = Queue()
user_mode = {}
user_file = {}
saved_name = {}
user_saved_thumb = {}
user_thumb_mode = {}
cancel_task = {}

# ===== UTILS =====
def smart(name):
    name = re.sub(r'@\w+|\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip().title() or "File"

def get_name(f):
    return f.document.file_name if f.document else "file"

def bar(p):
    return "█"*(p//10) + "░"*(10-p//10)

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
        [InlineKeyboardButton("⚡ Auto", callback_data="auto")],
        [InlineKeyboardButton("✏ Manual", callback_data="manual")],
        [InlineKeyboardButton("📌 Saved", callback_data="saved")]
    ])

def thumb_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Auto", callback_data="auto_thumb")],
        [InlineKeyboardButton("🖼 Saved", callback_data="saved_thumb")],
        [InlineKeyboardButton("🚫 No Thumb", callback_data="no_thumb")]
    ])

def progress_btn(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{uid}")],
        [InlineKeyboardButton("📢 AniToon's List", url=CHANNEL)]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(_, m):
    m.reply_text(
        "✨ **AniToons Rename Bot**\n\nFast | Clean | Powerful",
        reply_markup=main_menu()
    )

# ===== BUTTONS =====
@app.on_callback_query()
def cb(_, q):
    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "rename":
        user_mode[uid] = "wait_file"
        q.message.reply_text("📤 Send File")

    elif data == "settings":
    q.message.reply_text(
        "⚙ Settings Panel\n\n"
        "📌 Set Saved Name → Save default rename name\n"
        "🖼 Set Thumbnail → Save custom thumbnail\n\n"
        "👇 Choose option",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📌 Set Saved Name", callback_data="setname")],
            [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="setthumb")]
        ])
    )

elif data == "setname":
    user_mode[uid] = "setname"
    q.message.reply_text("✏ Send the name to save")

elif data == "setthumb":
    user_mode[uid] = "setthumb"
    q.message.reply_text("📸 Send thumbnail image")

    elif data == "auto":
        user_mode[uid] = "auto_thumb"
        q.message.reply_text("🖼 Choose Thumbnail", reply_markup=thumb_menu())

    elif data == "manual":
        user_mode[uid] = "manual_thumb"
        q.message.reply_text("🖼 Choose Thumbnail", reply_markup=thumb_menu())

elif data == "saved":
    if uid not in saved_name:
        user_mode[uid] = None
        q.message.reply_text(
            "❌ No saved name found!\n\n"
            "👉 Go to ⚙ Settings\n"
            "👉 Click 'Set Saved Name'\n"
            "👉 Then try again"
        )
        return

    user_mode[uid] = "saved_thumb"
    q.message.reply_text("🖼 Choose Thumbnail", reply_markup=thumb_menu())
        user_mode[uid] = "saved_thumb"
        q.message.reply_text("🖼 Choose Thumbnail", reply_markup=thumb_menu())

    elif data == "auto_thumb":
        user_thumb_mode[uid] = "auto"
        q.message.reply_text("📤 Send File")

    elif data == "saved_thumb":
        if uid not in user_saved_thumb:
            user_mode[uid] = "setthumb"
            q.message.reply_text("❌ No thumb saved\nSend image")
        else:
            user_thumb_mode[uid] = "saved"
            q.message.reply_text("📤 Send File")

    elif data == "no_thumb":
        user_thumb_mode[uid] = "none"
        q.message.reply_text("📤 Send File")

    elif data.startswith("cancel_"):
        cancel_task[uid] = True
        q.message.reply_text("❌ Cancelled")

# ===== FILE =====
@app.on_message(filters.document | filters.video | filters.audio)
def file(_, m):
    uid = m.from_user.id
    mode = user_mode.get(uid)

    if mode == "wait_file":
        user_file[uid] = m
        m.reply_text("Choose option", reply_markup=rename_menu())

    else:
        queue.put((m, "process", uid))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) == "manual_thumb":
        user_file[uid].text_name = m.text
        m.reply_text("🖼 Choose Thumbnail", reply_markup=thumb_menu())

    elif user_mode.get(uid) == "setname":
        saved_name[uid] = m.text
        m.reply_text("✅ Name Saved")

# ===== SAVE THUMB =====
@app.on_message(filters.photo)
def thumb(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) == "setthumb":
        path = m.download(f"{THUMB}/{uid}.jpg")
        user_saved_thumb[uid] = path
        m.reply_text("✅ Thumbnail Saved")

# ===== WORKER =====
def worker():
    while True:
        file, _, uid = queue.get()
        try:
            process(file, uid)
        except:
            try:
                file.reply_text("❌ Error")
            except:
                pass
        queue.task_done()

# ===== PROCESS =====
def process(file, uid):

    cancel_task[uid] = False

    msg = file.reply_text("⏳ Starting...", reply_markup=progress_btn(uid))
    start = time.time()

    def dprog(c, t):
        if cancel_task.get(uid):
            raise Exception()

        p = int(c*100/t)
        speed = c/(time.time()-start+1)
        eta = (t-c)/(speed+1)

        msg.edit_text(
            f"⬇ {bar(p)} {p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n⏱ {int(eta)}s",
            reply_markup=progress_btn(uid)
        )

    path = file.download(file_name=f"{DOWNLOAD}/{time.time()}", progress=dprog)

    msg.edit_text("⚙ Processing...", reply_markup=progress_btn(uid))

    name = saved_name.get(uid) or smart(get_name(file))
    ext = os.path.splitext(path)[1]
    out = f"{OUTPUT}/{name}{ext}"
    os.rename(path, out)

    thumb = None

    if user_thumb_mode.get(uid) == "saved":
        thumb = user_saved_thumb.get(uid)

    elif user_thumb_mode.get(uid) == "auto":
        thumb = f"{THUMB}/{time.time()}.jpg"
        subprocess.run(["ffmpeg","-i",out,"-ss","2","-vframes","1",thumb])

    msg.edit_text("⬆ Uploading...", reply_markup=progress_btn(uid))

    def uprog(c, t):
        if cancel_task.get(uid):
            raise Exception()

        p = int(c*100/t)
        msg.edit_text(
            f"⬆ {bar(p)} {p}%",
            reply_markup=progress_btn(uid)
        )

    if ext in [".mp4",".mkv"]:
        file.reply_video(
            out,
            caption=f"✅ {name}",
            thumb=thumb if thumb and os.path.exists(thumb) else None,
            supports_streaming=True,
            progress=uprog
        )
    else:
        file.reply_document(out, caption=f"✅ {name}", progress=uprog)

    try:
        os.remove(out)
    except:
        pass

# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            print("🚀 Running...")
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
