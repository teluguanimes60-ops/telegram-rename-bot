# ===== AniToons Rename Bot (FIXED v2) =====

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from flask import Flask
from config import *

import os, re, time, threading
from queue import Queue

# ===== CONFIG =====
WORKERS = 2
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
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

# ===== QUEUE =====
queue = Queue()

# ===== USER DATA =====
user_mode = {}
manual_name = {}
saved_name = {}
user_saved_thumb = {}
user_thumb_mode = {}
cancel_task = {}

# ===== CLEANUP =====
def cleanup(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

# ===== MENUS =====

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 Rename", callback_data="menu_rename"),
            InlineKeyboardButton("⚙ Settings", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("📢 Channel", url=CHANNEL)
        ]
    ])

def rename_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ Auto", callback_data="rename_auto"),
            InlineKeyboardButton("✏ Manual", callback_data="rename_manual")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main")
        ]
    ])

def thumb_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Auto Thumb", callback_data="thumb_auto"),
            InlineKeyboardButton("🖼 Saved Thumb", callback_data="thumb_saved")
        ],
        [
            InlineKeyboardButton("🚫 No Thumb", callback_data="thumb_none")
        ]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📌 Set Name", callback_data="set_name"),
            InlineKeyboardButton("🖼 Set Thumb", callback_data="set_thumb")
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

# ===== CALLBACK =====

@app.on_callback_query()
def cb(_, q):

    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "back_main":
        user_mode[uid] = None
        q.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

    elif data == "menu_rename":
        q.message.edit_text("Choose Rename Mode", reply_markup=rename_menu())

    elif data == "menu_settings":
        user_mode[uid] = None
        q.message.edit_text("⚙ Settings", reply_markup=settings_menu())

    elif data == "rename_auto":
        user_mode[uid] = "thumb"
        q.message.edit_text("Choose Thumbnail", reply_markup=thumb_menu())

    elif data == "rename_manual":
        user_mode[uid] = "rename_manual"
        q.message.edit_text("Send new file name")

    elif data == "thumb_auto":
        user_thumb_mode[uid] = "auto"
        user_mode[uid] = "ready"
        q.message.edit_text("Send file")

    elif data == "thumb_saved":
        if uid not in user_saved_thumb:
            user_mode[uid] = "set_thumb"
            q.message.edit_text("Send thumbnail first")
        else:
            user_thumb_mode[uid] = "saved"
            user_mode[uid] = "ready"
            q.message.edit_text("Send file")

    elif data == "thumb_none":
        user_thumb_mode[uid] = "none"
        user_mode[uid] = "ready"
        q.message.edit_text("Send file")

    elif data == "set_name":
        user_mode[uid] = "set_name"
        q.message.edit_text("Send name")

    elif data == "set_thumb":
        user_mode[uid] = "set_thumb"
        q.message.edit_text("Send thumbnail image")

    elif data.startswith("cancel_"):
        cancel_task[uid] = True
        q.message.edit_text("❌ Cancelled")

# ===== FILE HANDLER =====

@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # ===== READY → SEND TO QUEUE =====
    if mode == "ready":
        queue.put((m, uid, manual_name.get(uid)))
        m.reply_text("⏳ Added to queue...")
        return

    # ===== MANUAL RENAME STEP =====
    if mode == "rename_manual":
        user_mode[uid] = "get_name"
        manual_name[uid] = None
        m.reply_text("✏ Send new file name")
        return

    # ===== BLOCK =====
    if not mode:
        m.reply_text("❌ Use /start first")
        return


# ===== TEXT HANDLER =====

@app.on_message(filters.text & ~filters.command("start"))
def text_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # ===== GET MANUAL NAME =====
    if mode == "get_name":
        manual_name[uid] = m.text
        user_mode[uid] = "thumb"
        m.reply_text("🖼 Choose Thumbnail", reply_markup=thumb_menu())
        return

    # ===== SAVE NAME =====
    if mode == "set_name":
        saved_name[uid] = m.text
        user_mode[uid] = None
        m.reply_text("✅ Name Saved", reply_markup=main_menu())
        return

    # ===== DEFAULT =====
    if mode:
        m.reply_text("❌ Complete previous step")


# ===== PHOTO HANDLER =====

@app.on_message(filters.photo)
def photo_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # ===== SAVE THUMB =====
    if mode == "set_thumb":
        path = m.download(f"{THUMB}/{uid}.jpg")
        user_saved_thumb[uid] = path
        user_mode[uid] = None
        m.reply_text("✅ Thumbnail Saved", reply_markup=main_menu())
        return

    # ===== IGNORE =====
    m.reply_text("❌ Use this in Settings only")

# ===== WORKER SYSTEM =====

def worker():
    while True:
        m, uid, mname = queue.get()
        try:
            process(m, uid, mname)
        except Exception as e:
            print("Worker Error:", e)
        queue.task_done()


# ===== PROCESS FUNCTION =====

def process(file, uid, manual_name=None):

    cancel_task[uid] = False
    msg = file.reply_text("⏳ Processing...", reply_markup=progress_btn(uid))

    # ===== DOWNLOAD =====
    def dprog(c, t):
        if cancel_task.get(uid):
            raise Exception("Cancelled")
        percent = int(c * 100 / t)
        bar = "█" * (percent // 5) + "░" * (20 - percent // 5)
        safe_edit(msg, f"⬇ Downloading...\n[{bar}] {percent}%", progress_btn(uid))

    try:
        path = file.download(
            file_name=f"{DOWNLOAD}/{time.time()}",
            progress=dprog
        )
    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        safe_edit(msg, "❌ Download Failed")
        return

    # ===== FILE NAME =====
    base_name = manual_name or saved_name.get(uid) or file.file_name or "AniToons"
    base_name = re.sub(r'\.[^.]+$', '', base_name)  # remove extension
    base_name = base_name.strip()

    ext = os.path.splitext(file.file_name or "file.mp4")[1] or ".mp4"
    out = f"{OUTPUT}/{base_name}{ext}"

    try:
        os.rename(path, out)
    except Exception as e:
        print("RENAME ERROR:", e)
        safe_edit(msg, "❌ Rename Error")
        return

    if not os.path.exists(out):
        safe_edit(msg, "❌ File missing")
        return

    # ===== UPLOAD =====
    safe_edit(msg, "⬆ Uploading...", progress_btn(uid))

    def uprog(c, t):
        if cancel_task.get(uid):
            raise Exception("Cancelled")
        percent = int(c * 100 / t)
        bar = "█" * (percent // 5) + "░" * (20 - percent // 5)
        safe_edit(msg, f"⬆ Uploading...\n[{bar}] {percent}%", progress_btn(uid))

    try:
        # 🔥 IMPORTANT FIX (Render safe)
        if ext.lower() in [".mp4", ".mkv"]:
            file.reply_video(
                chat_id=uid,
                video=out,
                caption=f"✅ {base_name}",
                supports_streaming=True,
                progress=uprog
            )
        else:
            file.reply_document(
                chat_id=uid,
                document=out,
                caption=f"✅ {base_name}",
                progress=uprog
            )

    except Exception as e:
        print("UPLOAD ERROR:", e)
        safe_edit(msg, f"❌ Upload Failed\n{str(e)}")
        return

    # ===== CLEANUP =====
    cleanup(out)
    user_mode[uid] = None

    safe_edit(msg, "✅ Completed 🎉")

# ===== SAFE EDIT =====

def safe_edit(msg, text, btn=None):
    try:
        msg.edit_text(text, reply_markup=btn)
    except:
        pass


# ===== AUTO CLEANUP SYSTEM =====

def cleanup_all():
    while True:
        time.sleep(600)  # every 10 minutes

        for folder in [DOWNLOAD, OUTPUT, THUMB]:
            try:
                for file in os.listdir(folder):
                    full = os.path.join(folder, file)

                    if os.path.isfile(full):
                        os.remove(full)
            except Exception as e:
                print("CLEANUP ERROR:", e)


# ===== START CLEANER THREAD =====
threading.Thread(target=cleanup_all, daemon=True).start()

# ===== START WORKERS =====

def start_workers():
    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()


# ===== MAIN RUN =====

if __name__ == "__main__":

    print("🚀 AniToons Bot Starting...")

    # Start worker threads
    start_workers()

    # Start web server (for Render)
    threading.Thread(target=run_web, daemon=True).start()

    try:
        app.start()
        print("✅ Bot Started Successfully")

        idle()   # keeps bot alive

    except FloodWait as e:
        print(f"FloodWait: {e.value}")
        time.sleep(e.value)

    except Exception as e:
        print("Runtime Error:", e)

    finally:
        app.stop()
