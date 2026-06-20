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
    name = name.replace(".", " ").replace("_", " ")

    # Extract season & episode
    season = re.search(r'[Ss](\d+)', name)
    episode = re.search(r'[Ee](\d+)', name)

    s = f"S{season.group(1)}" if season else ""
    e = f"E{episode.group(1)}" if episode else ""

    # Extract quality
    quality = re.search(r'(480p|720p|1080p|2160p)', name, re.I)
    q = quality.group(1) if quality else ""

    # Extract language
    lang = re.search(r'(Hindi|English|Telugu|Tamil|Dual Audio)', name, re.I)
    l = lang.group(1) if lang else ""

    # Clean base name
    clean = re.sub(r'\[.*?\]|\(.*?\)|@\w+', '', name)
    clean = re.sub(r'(480p|720p|1080p|2160p)', '', clean, flags=re.I)
    clean = re.sub(r'(Hindi|English|Telugu|Tamil|Dual Audio)', '', clean, flags=re.I)
    clean = re.sub(r'[Ss]\d+|[Ee]\d+', '', clean)
    clean = re.sub(r'\d+$', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    final = f"{clean} {s}{e} {q} {l}".strip()
    return final.title() or "File"
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
        [
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{uid}")
        ],
        [
            InlineKeyboardButton("📢 Channel", url=CHANNEL)
        ]
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

    uid = q.from_user.id
    data = q.data
    q.answer()

    # ===== MAIN =====
    if data == "back_main":
        user_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_mode[uid] = None
        q.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

    # ===== RENAME MENU =====
@app.on_callback_query()
def cb(_, q):

    uid = q.from_user.id
    data = q.data
    q.answer()

    if data == "back_main":
        user_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_mode[uid] = None
        q.message.edit_text("🏠 Main Menu", reply_markup=main_menu())

    elif data == "menu_rename":
        q.message.edit_text("⚙ Choose Rename Type", reply_markup=rename_menu())

    elif data == "rename_auto":
        user_action[uid] = "rename"
        user_mode[uid] = "thumb"
        q.message.edit_text("🖼 Choose thumbnail", reply_markup=thumb_menu())

    elif data == "rename_manual":
        user_mode[uid] = "rename_manual"
        q.message.edit_text("✏ Send new file name")

    elif data == "rename_saved":
        user_action[uid] = "rename"
        user_mode[uid] = "thumb"
        q.message.edit_text("🖼 Choose thumbnail", reply_markup=thumb_menu())

    elif data == "convert_f2v":
        user_action[uid] = "convert"
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
# ===== FILE HANDLER (FIXED FINAL) =====

@app.on_message(filters.document | filters.video | filters.audio)
def file_handler(_, m):

    uid = m.from_user.id
    mode = user_mode.get(uid)

    # 🚫 BLOCK if user didn't press buttons
    if not mode:
        m.reply_text("❌ First select option from menu (/start)")
        return

    # ===== BULK MODE =====
    if bulk_mode.get(uid):
        bulk_files.setdefault(uid, []).append(m)
        m.reply_text(f"📦 File Added ({len(bulk_files[uid])})", reply_markup=bulk_menu())
        return

    # ===== WAITING STATES (DO NOTHING) =====
    if mode in [
        "rename_menu",
        "rename_auto_thumb",
        "rename_saved_thumb",
        "convert_f2v_thumb"
    ]:
        m.reply_text("❌ Complete previous step (choose thumbnail first)")
        return

    # ===== RENAME AUTO / SAVED =====
if mode == "ready":
    queue.put((m, uid))
    return
    # ===== MANUAL RENAME =====
    if mode == "rename_manual":
        user_file[uid] = m
        m.reply_text("✏ Send new name")
        return

    # ===== CONVERT =====
    if mode in ["convert_f2v", "convert_v2f"]:
        queue.put((m, uid))
        return

    # ❌ FALLBACK
    m.reply_text("❌ Invalid step, press /start again")

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
            [uid] = None
        return

    # ===== SET SAVED NAME =====
    if mode == "set_name":
        saved_name[uid] = m.text
        user_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_mode[uid] = None

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
        user_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_mode[uid] = None

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
    user_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_mode[uid] = None
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
    manual_name.pop(uid, None)
    name = re.sub(r'\d+$', '', name).strip()
    
    ext = os.path.splitext(path)[1]
    out = f"{OUTPUT}/{name}{ext}"

    os.rename(path, out)

    # ===== CONVERT =====
if user_action.get(uid) == "convert":
    new_out = f"{OUTPUT}/{time.time()}.mp4"

    subprocess.run([
        "ffmpeg", "-i", out,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        new_out
    ])

    cleanup(out)
    out = new_out
    ext = ".mp4"

# ===== THUMB =====
thumb = None
mode_thumb = user_thumb_mode.get(uid)

if mode_thumb == "saved":
    thumb = user_saved_thumb.get(uid)


    thumb = f"{THUMB}/{time.time()}.jpg"

    subprocess.run([
        "ffmpeg", "-i", out,
        "-ss", "00:00:01",
        "-vframes", "1",
        "-vf", "scale=320:320",
        "-q:v", "2",
        thumb
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not os.path.exists(thumb):
        thumb = None
        
    # ===== CONVERT =====

    thumb = f"{THUMB}/{time.time()}.jpg"
    try:
        subprocess.run([
            "ffmpeg", "-i", out,
            "-ss", "1",
            "-vframes", "1",
            "-vf", "scale=320:320",
            "-q:v", "2",
            thumb
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(thumb):
            thumb = None
    except:
        thumb = None
# ===== THUMB =====
 
    thumb = f"{THUMB}/{time.time()}.jpg"

    try:
        subprocess.run([
            "ffmpeg",
            "-i", out,
            "-ss", "00:00:01",
            "-vframes", "1",
            "-vf", "scale=320:320",
            "-q:v", "2",
            thumb
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(thumb):
            thumb = None

    except Exception as e:
        print("Thumbnail error:", e)
        thumb = None
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

    user_thumb_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_mode[uid] = None
    user_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_modeuser_mode[uid] = None

user_action = {}   # 🔥 ADD THIS LINE
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
