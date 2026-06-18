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
# 🔥 THUMB SYSTEM
user_thumb_mode = {}   # auto / saved
user_saved_thumb = {}  # thumbnail path
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

  if data == "convert":
    user_mode[uid] = "convert_select"
    q.message.reply_text(
        "🎬 Choose conversion type",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📹 File → Video", callback_data="f2v")],
            [InlineKeyboardButton("📁 Video → File", callback_data="v2f")]
        ])
    )

elif data == "f2v":
    user_mode[uid] = "f2v_thumb"
    q.message.reply_text(
        "🖼 Choose Thumbnail Mode",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Auto Thumbnail", callback_data="auto_thumb")],
            [InlineKeyboardButton("💾 Saved Thumbnail", callback_data="saved_thumb")]
        ])
    )

elif data == "auto_thumb":
    user_thumb_mode[uid] = "auto"
    user_mode[uid] = "f2v"
    q.message.reply_text("📤 Send file to convert into video")

elif data == "saved_thumb":
    if uid not in user_saved_thumb:
        user_mode[uid] = "save_thumb"
        q.message.reply_text("📸 Send thumbnail first")
    else:
        user_thumb_mode[uid] = "saved"
        user_mode[uid] = "f2v"
        q.message.reply_text("📤 Send file to convert")
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

# ===== SAVE THUMBNAIL =====
@app.on_message(filters.photo)
def save_thumb(_, m):
    uid = m.from_user.id

    if user_mode.get(uid) != "save_thumb":
        return

    path = m.download(f"{THUMB}/{uid}.jpg")
    user_saved_thumb[uid] = path
    user_mode[uid] = None

    m.reply_text("✅ Thumbnail Saved")

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

def process(file, name, uid):

    msg = file.reply_text("⏳ Starting...")

    start = time.time()

    # ===== DOWNLOAD =====
    def dprog(c, t):
        p = int(c*100/t)
        speed = c/(time.time()-start+1)
        eta = (t-c)/(speed+1)

        msg.edit_text(
            f"⬇ Downloading\n{p}%\n⚡ {round(speed/1024/1024,2)} MB/s\n⏱ ETA {int(eta)}s"
        )

    path = file.download(file_name=f"{DOWNLOAD}/{time.time()}", progress=dprog)

    msg.edit_text("⚙ Processing...")

    mode = user_mode.get(uid)

    # ===== CONVERT FILE → VIDEO =====
    if mode == "f2v":
        out = f"{OUTPUT}/{time.time()}.mp4"

        subprocess.run([
            "ffmpeg", "-i", path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-movflags", "+faststart",
            out
        ])

        path = out

    # ===== THUMB =====
    thumb = None

    if user_thumb_mode.get(uid) == "saved":
        thumb = user_saved_thumb.get(uid)

    elif user_thumb_mode.get(uid) == "auto":
        thumb = f"{THUMB}/{time.time()}.jpg"
        subprocess.run([
            "ffmpeg", "-i", path,
            "-ss", "2",
            "-vframes", "1",
            thumb
        ])

    # ===== UPLOAD =====
    msg.edit_text("⬆ Uploading...")

    def uprog(c, t):
        p = int(c*100/t)
        msg.edit_text(f"⬆ Uploading: {p}%")

    ext = os.path.splitext(path)[1]

    if ext == ".mp4":
        file.reply_video(
            path,
            caption="✅ Done",
            thumb=thumb if thumb and os.path.exists(thumb) else None,
            supports_streaming=True,
            progress=uprog
        )
    else:
        file.reply_document(
            path,
            caption="✅ Done",
            progress=uprog
        )
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
