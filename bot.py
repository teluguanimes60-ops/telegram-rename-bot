from pyrogram import Client, filters
from pyrogram.types import Message
from config import *
import os

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Store user state (simple memory)
user_state = {}

# ---------------- START ----------------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🤖 Rename Bot Ready!\n\n"
        "📁 Send any file to rename it."
    )

# ---------------- FILE RECEIVER ----------------
@app.on_message(filters.document | filters.video | filters.audio)
def get_file(_, message: Message):

    user_id = message.from_user.id

    # Save file info
    user_state[user_id] = {
        "file_id": message.id,
        "file": message
    }

    message.reply_text(
        "📁 File received!\n\n"
        "✏ Now send new file name (without extension)"
    )

# ---------------- RENAME HANDLER ----------------
@app.on_message(filters.text & ~filters.command("start"))
def rename_file(_, message: Message):

    user_id = message.from_user.id

    if user_id not in user_state:
        return message.reply_text("❌ First send a file!")

    new_name = message.text
    file_msg = user_state[user_id]["file"]

    # Download file
    file_path = file_msg.download()

    # Get extension
    ext = os.path.splitext(file_path)[1]

    new_file_path = f"{new_name}{ext}"

    os.rename(file_path, new_file_path)

    # Send renamed file
    message.reply_document(
        document=new_file_path,
        caption="✅ Renamed successfully!"

    )

    # Clear state
    del user_state[user_id]

    # Delete temp file
    os.remove(new_file_path)

app.run()
