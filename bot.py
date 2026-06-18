# ===== AniToons Rename Bot (FINAL STABLE VERSION) =====

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

# ===== WEB (IMPORTANT FOR RENDER) =====
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
user_thumb = {}

# ===== UTILS =====
def smart(name):
    name = re.sub(r'@\w+|\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip().title() or "File"

def get_name(f):
    return f.document.file_name if f.document else "file"

def progress_bar(p):
    return "█"*int(p/10) + "░"*(10-int(p/10))

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
        [InlineKeyboardButton("🤖 Auto Thumbnail", callback_data="auto_t")],
        [InlineKeyboardButton("🖼 Saved Thumbnail", callback_data="save_t")]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Set Saved Name", callback_data="setname")],
        [InlineKeyboardButton("🖼 Set Thumbnail", callback_data="setthumb")],
        [InlineKeyboardButton("👁 View Thumbnail", callback_data="viewthumb")]
    ])

def progress_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 AniToon's List", url=CHANNEL)]
    ])

# ===== START =====
@app.on_message(filters.command("start"))
def start(_, m):
    m.reply_text(
        "✨ **AniToons Rename Bot**\n\n"
        "⚡ Fast Rename\n🎬 Video Convert\n🖼 Thumbnail System\n\n"
        "👇 Choose option",
        reply_markup=main_menu()
    )

# ===== BUTTONS =====
@app.on_callback_query()
def cb(_, q):
    uid = q.from_user.id
    d = q.data
    q.answer()

    if d == "rename":
        user_mode[uid] = "wait_file"
        q.message.reply_text("📁 Send file to rename")

    elif d == "convert":
        user_mode[uid] = "convert_select"
        q.message.reply_text("🎬 Choose option", reply_markup=convert_menu())

    elif d == "settings":
        q.message.reply_text("⚙ Settings", reply_markup=settings_menu())

    elif d == "auto":
        f = user_file.get(uid)
        if f:
            queue.put((f, smart(get_name(f)), uid, "rename"))

    elif d == "manual":
        user_mode[uid] = "manual"
        q.message.reply_text("✏ Send new name")

    elif d == "saved":
        f = user_file.get(uid)
        if f:
            queue.put((f, saved_name.get(uid, "File"), uid, "rename"))

    elif d == "f2v":
        user_mode[uid] = "f2v"
        q.message.reply_text("Send file", reply_markup=thumb_menu())

    elif d == "v2f":
        user_mode[uid] = "v2f"
        q.message.reply_text("Send video", reply_markup=thumb_menu())

    elif d == "auto_t":
        user_mode[uid] += "_auto"

    elif d == "save_t":
        user_mode[uid] += "_saved"

    elif d == "setname":
        user_mode[uid] = "setname"
        q.message.reply_text("Send saved name")

    elif d == "setthumb":
        user_mode[uid] = "setthumb"
        q.message.reply_text("Send image")

    elif d == "viewthumb":
        t = user_thumb.get(uid)
        if t:
            q.message.reply_photo(t)
        else:
            q.message.reply_text("❌ No thumbnail set")

# ===== FILE HANDLER =====
@app.on_message(filters.document | filters.video | filters.audio)
def file(_, m):
    uid = m.from_user.id
    mode = user_mode.get(uid)

    if mode == "wait_file":
        user_file[uid] = m
        m.reply_text("Choose rename option", reply_markup=rename_menu())

    elif mode and ("f2v" in mode or "v2f" in mode):
        queue.put((m, "convert", uid, mode))

# ===== TEXT =====
@app.on_message(filters.text & ~filters.command("start"))
def text(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) == "manual":
        queue.put((user_file.get(uid), m.text, uid, "rename"))

    elif user_mode.get(uid) == "setname":
        saved_name[uid] = m.text
        m.reply_text("✅ Saved Name Updated")

# ===== THUMB =====
@app.on_message(filters.photo)
def thumb(_, m):
    uid = m.from_user.id
    if user_mode.get(uid) == "setthumb":
        path = m.download(f"{THUMB}/{uid}.jpg")
        user_thumb[uid] = path
        m.reply_text("✅ Thumbnail Saved")

# ===== WORKER =====
def worker():
    while True:
        file, name, uid, mode = queue.get()
        try:
            process(file, name, uid, mode)
        except:
            try:
                file.reply_text("❌ Failed")
            except:
                pass
        queue.task_done()

# ===== PROCESS =====
def process(file, name, uid, mode):

    msg = file.reply_text("⏳ Starting...", reply_markup=progress_btn())
    start = time.time()

    # DOWNLOAD
    def dprog(c, t):
        try:
            p = int(c*100/t)
            speed = c/(time.time()-start+1)
            eta = int((t-c)/(speed+1))

            msg.edit_text(
                f"⬇ Downloading...\n"
                f"{progress_bar(p)} {p}%\n"
                f"⚡ {round(speed/1024/1024,2)} MB/s\n"
                f"⏳ {eta}s left",
                reply_markup=progress_btn()
            )
        except:
            pass

    path = file.download(file_name=f"{DOWNLOAD}/{time.time()}", progress=dprog)

    if not path:
        msg.edit_text("❌ Download Failed")
        return

    msg.edit_text("⚙ Processing...", reply_markup=progress_btn())

    # CONVERT
    try:
        if "convert" in mode:
            if path.endswith(".mp4"):
                out = f"{OUTPUT}/{time.time()}.mkv"
                subprocess.run(["ffmpeg","-y","-i",path,"-c","copy",out])
            else:
                out = f"{OUTPUT}/{time.time()}.mp4"
                subprocess.run(["ffmpeg","-y","-i",path,out])
            path = out
    except:
        msg.edit_text("❌ Convert Failed")
        return

    # THUMB
    thumb = None
    try:
        if "auto" in mode:
            thumb = f"{THUMB}/{time.time()}.jpg"
            subprocess.run(["ffmpeg","-y","-i",path,"-ss","2","-vframes","1",thumb])
        else:
            thumb = user_thumb.get(uid)
    except:
        pass

    # RENAME
    ext = os.path.splitext(path)[1]
    new = f"{OUTPUT}/{name}{ext}"
    try:
        os.rename(path, new)
    except:
        new = path

    # UPLOAD
    def uprog(c, t):
        try:
            p = int(c*100/t)
            msg.edit_text(
                f"⬆ Uploading...\n{progress_bar(p)} {p}%",
                reply_markup=progress_btn()
            )
        except:
            pass

    try:
        if ext.lower() in [".mp4",".mkv",".mov"]:
            file.reply_video(
                video=new,
                caption=f"✅ {name}",
                thumb=thumb if thumb and os.path.exists(thumb) else None,
                supports_streaming=True,
                progress=uprog
            )
        else:
            file.reply_document(
                document=new,
                caption=f"✅ {name}",
                thumb=thumb if thumb and os.path.exists(thumb) else None,
                progress=uprog
            )

        msg.delete()

    except Exception as e:
        msg.edit_text(f"❌ Upload Failed\n{str(e)}")

    try:
        if os.path.exists(new):
            os.remove(new)
    except:
        pass

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
