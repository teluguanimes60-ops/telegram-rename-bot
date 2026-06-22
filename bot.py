# ===== AniToons Rename Bot (CLEAN PRO v1) =====

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from flask import Flask
from config import *

import os, re, time, threading, subprocess
from queue import Queue

# ===== CONFIG =====
WORKERS = 3
CHANNEL = "https://t.me/Anitoon_edit/33"

# ===== FOLDERS =====
BASE = os.getcwd()
DOWNLOAD = f"{BASE}/downloads"
OUTPUT = f"{BASE}/outputs"
THUMB = f"{BASE}/thumbs"

for p in [DOWNLOAD, OUTPUT, THUMB]:
    os.makedirs(p, exist_ok=True)

# ===== WEB SERVER =====
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ===== BOT CLIENT =====
app = Client(
    "AniToonsBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ===== DATABASE =====
queue = Queue()

# ===== USER STATES =====
user_mode = {}
user_file = {}
manual_name = {}

# ===== SETTINGS =====
saved_name = {}
user_saved_thumb = {}
user_thumb_mode = {}
user_action = {}   # 🔥 IMPORTANT

# ===== SYSTEM =====
cancel_task = {}

# ===== BULK =====
bulk_mode = {}
bulk_files = {}

# ===== CLEANUP =====
def cleanup(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

# ===== UI MENUS =====

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 Rename", callback_data="menu_rename"),
            InlineKeyboardButton("🎬 Convert", callback_data="menu_convert")
        ],
        [
            InlineKeyboardButton("📦 Bulk Mode", callback_data="menu_bulk"),
            InlineKeyboardButton("⚙ Settings", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("📢 AniToon's List", url=CHANNEL)
        ]
    ])

def rename_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Auto Rename", callback_data="rename_auto"),
            InlineKeyboardButton("✏ Manual Rename", callback_data="rename_manual")
        ],
        [
            InlineKeyboardButton("📌 Saved Rename", callback_data="rename_saved")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main")
        ]
    ])

def convert_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📹 File → Video", callback_data="convert_f2v"),
            InlineKeyboardButton("📁 Video → File", callback_data="convert_v2f")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main")
        ]
    ])

def thumb_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Auto Thumbnail", callback_data="thumb_auto"),
            InlineKeyboardButton("🖼 Saved Thumbnail", callback_data="thumb_saved")
        ],
        [
            InlineKeyboardButton("🚫 No Thumbnail", callback_data="thumb_none")
        ]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📌 Set Name", callback_data="set_name"),
            InlineKeyboardButton("🖼 Set Thumbnail", callback_data="set_thumb")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main")
        ]
    ])

def bulk_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶ Start Bulk", callback_data="start_bulk"),
            InlineKeyboardButton("❌ Cancel Bulk", callback_data="cancel_bulk")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main")
        ]
    ])

def progress_btn(uid):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Channel", url=CHANNEL),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{uid}")
        ]
    ])

# ===== START =====

@app.on_message(filters.command("start"))
def start(_, m):
    user_mode[m.from_user.id] = None

    m.reply_text(
        "✨ **AniToons Bot Ready**\n\nChoose an option 👇",
        reply_markup=main_menu()
    )
        
@app.on_callback_query()
def cb(_, q):

    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "back_main":
        user_mode[uid] = None
        q.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

    elif data == "menu_rename":
        q.message.edit_text("⚙ Choose Rename Type", reply_markup=rename_menu())

    elif data == "menu_convert":
        q.message.edit_text("🎬 Choose Convert Type", reply_markup=convert_menu())

    elif data == "convert_f2v":
        user_action[uid] = "convert"
        user_mode[uid] = "rename_choice"
        q.message.edit_text("✏ Choose rename type", reply_markup=rename_menu())

    elif data == "convert_v2f":
        user_action[uid] = "convert"
        user_mode[uid] = "rename_choice"
        q.message.edit_text("✏ Choose rename type", reply_markup=rename_menu())

    elif data == "rename_auto":
        user_action[uid] = "rename"
        user_mode[uid] = "thumb"
        q.message.edit_text("🖼 Choose thumbnail", reply_markup=thumb_menu())

    elif data == "rename_manual":
        user_mode[uid] = "rename_manual"
        q.message.edit_text("✏ Send new file name")

    elif data == "rename_saved":
        if uid not in saved_name:
            q.message.edit_text(
                "❌ You didn't set saved name\n\n👉 Go to Settings first",
                reply_markup=settings_menu()
            )
            return

        user_action[uid] = "rename"
        user_mode[uid] = "thumb"
        q.message.edit_text("🖼 Choose thumbnail", reply_markup=thumb_menu())

    elif data == "thumb_auto":
        user_thumb_mode[uid] = "auto"
        user_mode[uid] = "ready"
        q.message.edit_text("📤 Send file")

    elif data == "thumb_saved":
        if uid not in user_saved_thumb:
            user_mode[uid] = "set_thumb"
            q.message.edit_text("❌ Send thumbnail first")
        else:
            user_thumb_mode[uid] = "saved"
            user_mode[uid] = "ready"
            q.message.edit_text("📤 Send file")

    elif data == "thumb_none":
        user_thumb_mode[uid] = "none"
        user_mode[uid] = "ready"
        q.message.edit_text("📤 Send file")

    elif data.startswith("cancel_"):
        cancel_task[uid] = True
        q.message.edit_text("❌ Cancelled")
# ===== FILE HANDLER =====

@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # ===== READY (MAIN PROCESS) =====
    if mode == "ready":
        queue.put((m, uid))
        return

    # ===== BULK MODE =====
    if bulk_mode.get(uid):
        bulk_files.setdefault(uid, []).append(m)
        m.reply_text(f"📦 Added ({len(bulk_files[uid])})", reply_markup=bulk_menu())
        return

    # ===== MANUAL RENAME =====
    if mode == "rename_manual":
        user_file[uid] = m
        m.reply_text("✏ Now send new file name")
        return

    # ===== BLOCK IF NOTHING SELECTED =====
    if not mode:
        m.reply_text("❌ First press /start and choose option")
        return

# ===== TEXT HANDLER =====

@app.on_message(filters.text & ~filters.command("start"))
def text_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # ===== MANUAL RENAME NAME INPUT =====
    if mode == "rename_manual":
        manual_name[uid] = m.text
        user_mode[uid] = "thumb"

        m.reply_text("🖼 Choose Thumbnail", reply_markup=thumb_menu())
        return

    # ===== SET SAVED NAME =====
    if mode == "set_name":
        saved_name[uid] = m.text
        user_mode[uid] = None

        m.reply_text("✅ Saved Name Updated", reply_markup=main_menu())
        return

    # ===== DEFAULT =====
    if mode:
        m.reply_text("❌ Complete previous step properly")

# ===== PHOTO HANDLER (THUMBNAIL) =====

@app.on_message(filters.photo)
def photo_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # ===== SAVE THUMBNAIL =====
    if mode == "set_thumb":
        path = m.download(f"{THUMB}/{uid}.jpg")
        user_saved_thumb[uid] = path
        user_mode[uid] = None

        m.reply_text("✅ Thumbnail Saved", reply_markup=main_menu())
        return

    # ===== IGNORE OTHER PHOTOS =====
    m.reply_text("❌ Use this only in Settings → Set Thumbnail")

# ===== WORKER SYSTEM =====

def worker():
    while True:
        data = queue.get()

        try:
            if len(data) == 3:
                process(data[0], data[1], data[2])
            else:
                process(data[0], data[1])
        except Exception as e:
            print("Worker Error:", e)

        queue.task_done()


# ===== START WORKERS =====
def start_workers():
    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

def process(file, uid, manual_name=None):

    cancel_task[uid] = False
    msg = file.reply_text("⏳ Starting...", reply_markup=progress_btn(uid))

# ===== DOWNLOAD =====
    def dprog(c, t):
        if cancel_task.get(uid):
            raise Exception("Cancelled")

        percent = int(c * 100 / t)
        filled = percent // 5
        bar = "█" * filled + "░" * (20 - filled)

        safe_edit(msg, f"⬇ Downloading...\n\n[{bar}]\n\n⚡ {percent}%", progress_btn(uid))

    try:
        path = file.download(
            file_name=f"{DOWNLOAD}/{time.time()}",
            progress=dprog
        )
    except Exception:
        safe_edit(msg, "❌ Download Cancelled")
        return
        
    # ===== FILE NAME =====
    name = manual_name or saved_name.get(uid) or getattr(file, "file_name", None) or "AniToons"
    name = re.sub(r'\d+$', '', name).strip()

    ext = os.path.splitext(file.file_name or "file.mp4")[1]
    if not ext:
        ext = ".mp4"

    out = f"{OUTPUT}/{name}{ext}"

    try:
        os.rename(path, out)
    except Exception as e:
        safe_edit(msg, f"❌ Rename Error\n{str(e)}")
        return
    # ===== CONVERT =====
    if user_action.get(uid) == "convert":
        new_out = f"{OUTPUT}/{time.time()}.mp4"

        safe_edit(msg, "🎬 Converting...", progress_btn(uid))

        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        subprocess.run([
            ffmpeg_path,
            "-y",
            "-i", out,
            new_out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        cleanup(out)
        out = new_out
        ext = ".mp4"

# ===== UPLOAD =====
    last_update = {}
    start_time = time.time()

    def uprog(current, total):
        if cancel_task.get(uid):
            raise Exception("Cancelled")

        now = time.time()

        # reduce spam edits (fast + smooth)
        if uid in last_update and now - last_update[uid] < 0.8:
            return
        last_update[uid] = now

        percent = int(current * 100 / total)
        filled = percent // 5
        bar = "█" * filled + "░" * (20 - filled)

        speed = current / max(1, now - start_time)
        speed = speed / 1024 / 1024  # MB/s

        safe_edit(
            msg,
            f"⬆ Uploading...\n\n[{bar}] {percent}%\n\n⚡ {speed:.2f} MB/s",
            progress_btn(uid)
        )

    try:
        if ext in [".mp4", ".mkv"]:
            app.send_video(
                chat_id=uid,
                video=out,
                caption=f"✅ {name}",
                supports_streaming=True,
                progress=uprog
            )
        else:
            app.send_document(
                chat_id=uid,
                document=out,
                caption=f"✅ {name}",
                progress=uprog
            )

    except Exception as e:
        safe_edit(msg, f"❌ Upload Failed\n{str(e)}")
        return

    # ===== CLEAN =====
    cleanup(out)
    user_mode[uid] = None
    user_action[uid] = None

    safe_edit(msg, "✅ Completed 🎉")
# ===== BULK SYSTEM =====

def process_bulk(uid):
    files = bulk_files.get(uid, [])

    if not files:
        return

    total = len(files)
    done = 0

    msg = app.send_message(uid, f"🚀 Starting Bulk\nTotal: {total}")

    for f in files:
        try:
            process(f, uid)
            done += 1
            msg.edit_text(f"📦 Progress: {done}/{total}")
        except:
            msg.edit_text(f"⚠ Error at {done+1}")

    bulk_files[uid] = []
    bulk_mode[uid] = False

    msg.edit_text("✅ Bulk Completed")


# ===== BULK COMMAND =====

@app.on_message(filters.command("bulk"))
def bulk_start(_, m):
    uid = m.from_user.id

    bulk_mode[uid] = True
    bulk_files[uid] = []

    m.reply_text(
        "📦 Bulk Mode ON\n\nSend files then press Start",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶ Start Bulk", callback_data="start_bulk")],
            [InlineKeyboardButton("❌ Cancel Bulk", callback_data="cancel_bulk")]
        ])
    )

# ===== CLEANUP SYSTEM =====

def cleanup_all():
    while True:
        time.sleep(600)  # every 10 min

        for folder in [DOWNLOAD, OUTPUT, THUMB]:
            for file in os.listdir(folder):
                try:
                    full = os.path.join(folder, file)
                    if os.path.isfile(full):
                        os.remove(full)
                except:
                    pass

# ===== SAFE EDIT =====

def safe_edit(msg, text, btn=None):
    try:
        msg.edit_text(text, reply_markup=btn)
    except:
        pass

# ===== START WORKERS =====

def worker():
    while True:
        data = queue.get()

        try:
            if len(data) == 3:
                process(data[0], data[1], data[2])
            else:
                process(data[0], data[1])
        except Exception as e:
            print("Worker Error:", e)

        queue.task_done()


# ===== START CLEANER THREAD =====
threading.Thread(target=cleanup_all, daemon=True).start()


# ===== RUN BOT =====
if __name__ == "__main__":

    # Start workers
    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    # Start web server
    threading.Thread(target=run_web, daemon=True).start()

    print("🚀 AniToons Bot Running...")

    while True:
        try:
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
        except Exception as e:
            print("Error:", e)
            time.sleep(5)
