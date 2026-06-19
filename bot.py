# ===== AniToons Rename Bot (ULTRA PRO MAX) =====

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

# 🔥 BULK + PREMIUM
bulk_mode = {}
bulk_files = {}
premium_users = set()   # add user ids manually here

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
        [InlineKeyboardButton("📁 Rename", callback_data="menu_rename"),
         InlineKeyboardButton("🎬 Convert", callback_data="menu_convert")],
        [InlineKeyboardButton("⚙ Settings", callback_data="menu_settings")],
        [InlineKeyboardButton("📢 AniToon's List", url=CHANNEL)]
    ])

def back_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
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
        "✨ **AniToons Rename Bot**\n\n"
        "⚡ Fast Rename\n🎬 Convert\n🖼 Thumbnail System\n\n"
        "👇 Choose option",
        reply_markup=main_menu()
    )
# ===== BUTTONS =====
@app.on_callback_query()
def cb(_, q):

    uid = q.from_user.id
    data = q.data

    # ===== MAIN MENU =====
    if data == "back_main":
        q.message.edit_text(
            "✨ AniToons Rename Bot\nChoose option 👇",
            reply_markup=main_menu()
        )

    # ===== RENAME MENU =====
    elif data == "menu_rename":
        user_mode[uid] = "wait_file"
        q.message.edit_text(
            "📁 Send file to rename",
            reply_markup=back_btn()
        )

    # ===== CONVERT MENU =====
    elif data == "menu_convert":
        q.message.edit_text(
            "🎬 Choose convert type",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📹 File → Video", callback_data="f2v")],
                [InlineKeyboardButton("📁 Video → File", callback_data="v2f")],
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ])
        )

    # ===== FILE → VIDEO =====
    elif data == "f2v":
        user_mode[uid] = "f2v_thumb"
        q.message.edit_text(
            "🖼 Choose thumbnail",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Auto", callback_data="auto_thumb")],
                [InlineKeyboardButton("🖼 Saved", callback_data="saved_thumb")],
                [InlineKeyboardButton("🚫 No Thumb", callback_data="no_thumb")],
                [InlineKeyboardButton("🔙 Back", callback_data="menu_convert")]
            ])
        )

    # ===== THUMB OPTIONS =====
    elif data == "auto_thumb":
        user_thumb_mode[uid] = "auto"
        user_mode[uid] = "f2v"
        q.message.edit_text("📤 Send file now", reply_markup=back_btn())

    elif data == "saved_thumb":
        if uid not in user_saved_thumb:
            user_mode[uid] = "setthumb"
            q.message.edit_text(
                "❌ No saved thumbnail!\n📸 Send thumbnail first",
                reply_markup=back_btn()
            )
        else:
            user_thumb_mode[uid] = "saved"
            user_mode[uid] = "f2v"
            q.message.edit_text("📤 Send file now", reply_markup=back_btn())

    elif data == "no_thumb":
        user_thumb_mode[uid] = "none"
        user_mode[uid] = "f2v"
        q.message.edit_text("📤 Send file now", reply_markup=back_btn())
# ===== FILE =====
@app.on_message(filters.document | filters.video | filters.audio)
def file(_, m):
    uid = m.from_user.id

    # BULK
if bulk_mode.get(uid):
    bulk_files.setdefault(uid, []).append(m)
    m.reply_text(f"📦 Added {len(bulk_files[uid])} files\nClick 'Start Bulk'")
    return

    if user_mode.get(uid) == "wait_file":
        user_file[uid] = m
        m.reply_text("Choose option", reply_markup=rename_menu())
    else:
        queue.put((m, uid))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) == "manual":
        queue.put((user_file[uid], uid, m.text))

    elif user_mode.get(uid) == "setname":
        saved_name[uid] = m.text
        m.reply_text("✅ Saved")

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
        data = queue.get()
        try:
            if len(data) == 3:
                process(data[0], data[1], data[2])
            else:
                process(data[0], data[1])
        except:
            pass
        queue.task_done()

# ===== PROCESS =====
def process(file, uid, manual_name=None):

    cancel_task[uid] = False
    msg = file.reply_text("⏳ Starting...", reply_markup=progress_btn(uid))

    start = time.time()

    def dprog(c, t):
        if cancel_task.get(uid): raise Exception()
        p = int(c*100/t)
        msg.edit_text(f"⬇ {bar(p)} {p}%", reply_markup=progress_btn(uid))

    path = file.download(file_name=f"{DOWNLOAD}/{time.time()}", progress=dprog)

    name = manual_name or saved_name.get(uid) or smart(get_name(file))

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
        if cancel_task.get(uid): raise Exception()
        p = int(c*100/t)
        msg.edit_text(f"⬆ {bar(p)} {p}%", reply_markup=progress_btn(uid))

    if ext in [".mp4",".mkv"]:
        file.reply_video(out, caption=name, thumb=thumb if thumb else None, supports_streaming=True, progress=uprog)
    else:
        file.reply_document(out, caption=name, progress=uprog)

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
