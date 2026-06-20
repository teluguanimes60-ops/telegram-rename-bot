# ===== AniToons Rename Bot (ULTRA PRO MAX v2) =====

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
TEMP = f"{BASE}/temp"

for p in [DOWNLOAD, OUTPUT, THUMB, TEMP]:
    os.makedirs(p, exist_ok=True)

# ===== WEB SERVER (RENDER KEEP ALIVE) =====
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

# ===== DATABASE (MEMORY) =====
queue = Queue()

# user states
user_mode = {}          # rename / convert / etc
user_step = {}          # step tracking
user_file = {}          # last file
manual_name = {}        # manual rename

# saved features
saved_name = {}         # saved rename name
user_saved_thumb = {}   # saved thumbnail path
user_thumb_mode = {}    # auto / saved / none

# cancel system
cancel_task = {}

# ===== BULK SYSTEM =====
bulk_mode = {}          # True / False
bulk_files = {}         # list of files

# ===== PREMIUM SYSTEM =====
premium_users = set()   # add IDs manually
FREE_LIMIT = 2          # free users limit
user_daily_count = {}

# ===== SECURITY / CLEANUP =====
def cleanup(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass
# ===== UTILS =====

def smart(name):
    name = re.sub(r'@\w+|\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip().title() or "File"

def get_name(f):
    if f.document:
        return f.document.file_name
    elif f.video:
        return f.video.file_name or "video.mp4"
    elif f.audio:
        return f.audio.file_name or "audio.mp3"
    return "file"

def bar(p):
    return "█"*(p//10) + "░"*(10 - p//10)

def format_size(size):
    for unit in ["B","KB","MB","GB"]:
        if size < 1024:
            return f"{round(size,2)} {unit}"
        size /= 1024

def speed_eta(start, current, total):
    speed = current / (time.time() - start + 1)
    eta = (total - current) / (speed + 1)
    return round(speed/1024/1024,2), int(eta)


# ===== UI SYSTEM (ADVANCED EDIT MENU) =====

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

def back_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
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

def thumb_menu(back_to="back_main"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Auto Thumbnail", callback_data="thumb_auto"),
            InlineKeyboardButton("🖼 Saved Thumbnail", callback_data="thumb_saved")
        ],
        [
            InlineKeyboardButton("🚫 No Thumbnail", callback_data="thumb_none")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data=back_to)
        ]
    ])

def settings_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📌 Set Saved Name", callback_data="set_name"),
            InlineKeyboardButton("🖼 Set Thumbnail", callback_data="set_thumb")
        ],
        [
            InlineKeyboardButton("👁 View Thumbnail", callback_data="view_thumb")
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
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{uid}")]
    ])


# ===== START MESSAGE =====

@app.on_message(filters.command("start"))
def start(_, m):
    m.reply_text(
        "✨ **AniToons Ultra Bot**\n\n"
        "⚡ Rename Files\n"
        "🎬 Convert Video\n"
        "📦 Bulk System\n"
        "🖼 Thumbnail Control\n\n"
        "👇 Choose option",
        reply_markup=main_menu()
    )
    # ===== BUTTON HANDLER (ADVANCED UI FLOW) =====

@app.on_callback_query()
def cb(_, q):

    uid = q.from_user.id
    data = q.data
    q.answer()

    # ===== MAIN =====
    if data == "back_main":
        user_mode[uid] = None
        q.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

    # ===== RENAME MENU =====
    elif data == "menu_rename":
        user_mode[uid] = "wait_file"
        q.message.edit_text("📤 Send file to rename", reply_markup=back_main())

    elif data == "rename_auto":
        user_mode[uid] = "rename_auto_thumb"
        q.message.edit_text("🖼 Choose thumbnail", reply_markup=thumb_menu("menu_rename"))

    elif data == "rename_manual":
        user_mode[uid] = "rename_manual"
        q.message.edit_text("✏ Send new file name")

    elif data == "rename_saved":
        if uid not in saved_name:
            q.message.edit_text(
                "❌ No saved name found!\n\n"
                "👉 Go to Settings\n👉 Set Saved Name",
                reply_markup=back_main()
            )
        else:
            user_mode[uid] = "rename_saved_thumb"
            q.message.edit_text("🖼 Choose thumbnail", reply_markup=thumb_menu("menu_rename"))

    # ===== CONVERT MENU =====
    elif data == "menu_convert":
        q.message.edit_text("🎬 Convert Options", reply_markup=convert_menu())

    elif data == "convert_f2v":
        user_mode[uid] = "convert_f2v_thumb"
        q.message.edit_text("🖼 Choose thumbnail", reply_markup=thumb_menu("menu_convert"))

    elif data == "convert_v2f":
        user_mode[uid] = "convert_v2f"
        q.message.edit_text("📤 Send video to convert into file", reply_markup=back_main())

    # ===== BULK MODE =====
    elif data == "menu_bulk":
        bulk_mode[uid] = True
        bulk_files[uid] = []
        q.message.edit_text(
            "📦 Bulk Mode Enabled\n\n📤 Send multiple files",
            reply_markup=bulk_menu()
        )

    elif data == "start_bulk":
        files = bulk_files.get(uid, [])

        if not files:
            q.answer("No files added!", show_alert=True)
            return

        q.message.edit_text(f"🚀 Processing {len(files)} files...")

        for f in files:
            queue.put((f, uid))

        bulk_files[uid] = []

    elif data == "cancel_bulk":
        bulk_mode[uid] = False
        bulk_files[uid] = []
        q.message.edit_text("❌ Bulk Cancelled", reply_markup=main_menu())

    # ===== SETTINGS =====
    elif data == "menu_settings":
        q.message.edit_text("⚙ Settings Panel", reply_markup=settings_menu())

    elif data == "set_name":
        user_mode[uid] = "set_name"
        q.message.edit_text("✏ Send name to save", reply_markup=back_main())

    elif data == "set_thumb":
        user_mode[uid] = "set_thumb"
        q.message.edit_text("📸 Send thumbnail image", reply_markup=back_main())

    elif data == "view_thumb":
        thumb = user_saved_thumb.get(uid)

        if thumb and os.path.exists(thumb):
            q.message.reply_photo(thumb, caption="🖼 Your Saved Thumbnail")
        else:
            q.message.reply_text("❌ No thumbnail saved")

    # ===== THUMB OPTIONS =====
    elif data == "thumb_auto":
        user_thumb_mode[uid] = "auto"

        if "convert" in str(user_mode.get(uid)):
            user_mode[uid] = "convert_f2v"
        else:
            user_mode[uid] = "rename_auto"

        q.message.edit_text("📤 Send file", reply_markup=back_main())

    elif data == "thumb_saved":
        if uid not in user_saved_thumb:
            user_mode[uid] = "set_thumb"
            q.message.edit_text(
                "❌ No saved thumbnail!\n\n📸 Send thumbnail first",
                reply_markup=back_main()
            )
        else:
            user_thumb_mode[uid] = "saved"

            if "convert" in str(user_mode.get(uid)):
                user_mode[uid] = "convert_f2v"
            else:
                user_mode[uid] = "rename_auto"

            q.message.edit_text("📤 Send file", reply_markup=back_main())

    elif data == "thumb_none":
        user_thumb_mode[uid] = "none"

        if "convert" in str(user_mode.get(uid)):
            user_mode[uid] = "convert_f2v"
        else:
            user_mode[uid] = "rename_auto"

        q.message.edit_text("📤 Send file", reply_markup=back_main())

    # ===== CANCEL =====
    elif data.startswith("cancel_"):
        cancel_task[uid] = True
        q.message.edit_text("❌ Task Cancelled", reply_markup=main_menu())
# ===== FILE HANDLER (MAIN ENGINE INPUT) =====

@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, m):

    uid = m.from_user.id

    # ===== BULK MODE =====
    if bulk_mode.get(uid):
        bulk_files.setdefault(uid, []).append(m)

        m.reply_text(
            f"📦 File Added\nTotal Files: {len(bulk_files[uid])}",
            reply_markup=bulk_menu()
        )
        return

mode = user_mode.get(uid)

# 🚫 BLOCK if user didn't select anything
if not mode:
    m.reply_text("❌ First choose option from menu (/start)")
    return

# ===== WAIT FILE FOR RENAME =====
if mode == "wait_file":
    user_file[uid] = m
    m.reply_text("⚙ Choose Rename Type", reply_markup=rename_menu())
    return

# ===== VALID MODES ONLY =====
allowed = [
    "rename_auto",
    "rename_saved",
    "rename_manual",
    "convert_f2v",
    "convert_v2f"
]

if mode not in allowed:
    m.reply_text("❌ Complete previous step first")
    return

# ===== PROCESS =====
if mode == "rename_manual":
    user_file[uid] = m
    m.reply_text("✏ Send new name")
else:
    queue.put((m, uid))


# ===== TEXT HANDLER =====

@app.on_message(filters.text & ~filters.command("start"))
def text_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # ===== MANUAL RENAME NAME INPUT =====
    if mode == "rename_manual":
        manual_name[uid] = m.text
        user_mode[uid] = "rename_manual_thumb"

        m.reply_text("🖼 Choose thumbnail", reply_markup=thumb_menu("menu_rename"))
        return

    # ===== AFTER MANUAL NAME → FILE PROCESS =====
    if mode == "rename_manual_thumb":
        if uid in user_file:
            queue.put((user_file[uid], uid, manual_name.get(uid)))
            user_mode[uid] = None
        return

    # ===== SET SAVED NAME =====
    if mode == "set_name":
        saved_name[uid] = m.text
        user_mode[uid] = None

        m.reply_text("✅ Saved Name Updated", reply_markup=main_menu())
        return


# ===== PHOTO HANDLER (THUMBNAIL) =====

@app.on_message(filters.photo)
def photo_handler(_, m):

    uid = m.from_user.id

    # ===== SAVE THUMB =====
    if user_mode.get(uid) == "set_thumb":
        path = m.download(f"{THUMB}/{uid}.jpg")
        user_saved_thumb[uid] = path
        user_mode[uid] = None

        m.reply_text("✅ Thumbnail Saved", reply_markup=main_menu())
        return

    # ===== IGNORE OTHER PHOTOS =====
    m.reply_text("❌ Use this only in thumbnail settings")


# ===== BULK CLEANER (OPTIONAL SAFETY) =====

def bulk_cleanup(uid):
    try:
        for f in bulk_files.get(uid, []):
            del f
        bulk_files[uid] = []
    except:
        pass


# ===== AUTO RESET USER STATE =====

def reset_user(uid):
    user_mode[uid] = None
    user_file.pop(uid, None)
    manual_name.pop(uid, None)

# ===== WORKER =====
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
        
    # ===== BULK PROCESS ENGINE =====

def process_bulk(uid):
    files = bulk_files.get(uid, [])
    if not files:
        return

    total = len(files)
    done = 0

    msg = app.send_message(uid, f"🚀 Starting Bulk Rename\nTotal: {total}")

    for f in files:
        try:
            process(f, uid)
            done += 1
            msg.edit_text(f"📦 Bulk Progress\nDone: {done}/{total}")
        except:
            msg.edit_text(f"⚠️ Error on file {done+1}")

    bulk_files[uid] = []
    bulk_mode[uid] = False

    msg.edit_text("✅ Bulk Completed")


# ===== CLEANUP SYSTEM =====

def cleanup(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass


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


# ===== SAFE EDIT (ANTI ERROR) =====

def safe_edit(msg, text, btn=None):
    try:
        msg.edit_text(text, reply_markup=btn)
    except:
        pass


# ===== PROCESS FINAL FIXED =====

def process(file, uid, manual_name=None):

    cancel_task[uid] = False

    msg = file.reply_text("⏳ Starting...", reply_markup=progress_btn(uid))
    start = time.time()

    # ===== DOWNLOAD =====
    def dprog(c, t):
        if cancel_task.get(uid):
            raise Exception()

        p = int(c * 100 / t)
        speed = c / (time.time() - start + 1)

        safe_edit(
            msg,
            f"⬇ {bar(p)} {p}%\n⚡ {round(speed/1024/1024,2)} MB/s",
            progress_btn(uid)
        )

    try:
        path = file.download(
            file_name=f"{DOWNLOAD}/{time.time()}",
            progress=dprog
        )
    except:
        safe_edit(msg, "❌ Cancelled")
        return

    # ===== NAME =====
    name = manual_name or saved_name.get(uid) or smart(get_name(file))

    ext = os.path.splitext(path)[1]
    out = f"{OUTPUT}/{name}{ext}"

    os.rename(path, out)

    # ===== CONVERT =====
    if user_mode.get(uid) == "f2v":
        new_out = f"{OUTPUT}/{time.time()}.mp4"

        subprocess.run([
            "ffmpeg", "-i", out,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-movflags", "+faststart",
            new_out
        ])

        cleanup(out)
        out = new_out
        ext = ".mp4"

    # ===== THUMB =====
    thumb = None

    if user_thumb_mode.get(uid) == "saved":
        thumb = user_saved_thumb.get(uid)

    elif user_thumb_mode.get(uid) == "auto":
        thumb = f"{THUMB}/{time.time()}.jpg"
        subprocess.run([
            "ffmpeg", "-i", out,
            "-ss", "2",
            "-vframes", "1",
            thumb
        ])

    # ===== UPLOAD =====
    safe_edit(msg, "⬆ Uploading...", progress_btn(uid))

    def uprog(c, t):
        if cancel_task.get(uid):
            raise Exception()

        p = int(c * 100 / t)

        safe_edit(
            msg,
            f"⬆ {bar(p)} {p}%",
            progress_btn(uid)
        )

    try:
        if ext in [".mp4", ".mkv"]:
            file.reply_video(
                out,
                caption=f"✅ {name}",
                thumb=thumb if thumb and os.path.exists(thumb) else None,
                supports_streaming=True,
                progress=uprog
            )
        else:
            file.reply_document(
                out,
                caption=f"✅ {name}",
                progress=uprog
            )
    except:
        safe_edit(msg, "❌ Upload Cancelled")
        return

    # ===== FINAL CLEAN =====
    cleanup(out)
    if thumb and "auto" in thumb:
        cleanup(thumb)

    safe_edit(msg, "✅ Completed")


# ===== EXTRA COMMANDS =====

@app.on_message(filters.command("bulk"))
def bulk_start(_, m):
    uid = m.from_user.id
    bulk_mode[uid] = True
    bulk_files[uid] = []

    m.reply_text(
        "📦 Bulk Mode ON\n\nSend multiple files\nThen click Start Bulk",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶ Start Bulk", callback_data="start_bulk")],
            [InlineKeyboardButton("❌ Cancel Bulk", callback_data="cancel_bulk")]
        ])
    )


@app.on_callback_query(filters.regex("start_bulk"))
def start_bulk(_, q):
    uid = q.from_user.id

    files = bulk_files.get(uid, [])
    if not files:
        q.answer("No files!", show_alert=True)
        return

    q.message.edit_text(f"🚀 Starting Bulk ({len(files)} files)")
    threading.Thread(target=process_bulk, args=(uid,)).start()


@app.on_callback_query(filters.regex("cancel_bulk"))
def cancel_bulk(_, q):
    uid = q.from_user.id

    bulk_mode[uid] = False
    bulk_files[uid] = []

    q.message.edit_text("❌ Bulk Cancelled", reply_markup=main_menu())


# ===== AUTO CLEAN THREAD =====
threading.Thread(target=cleanup_all, daemon=True).start()


# ===== RUN =====
if __name__ == "__main__":

    for _ in range(WORKERS):
        threading.Thread(target=worker, daemon=True).start()

    threading.Thread(target=run_web, daemon=True).start()

    print("🚀 ULTRA PRO MAX BOT RUNNING...")

    while True:
        try:
            app.run()
        except FloodWait as e:
            time.sleep(e.value)
        except Exception as e:
            print("Error:", e)
            time.sleep(5)
