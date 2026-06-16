from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
import os

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Store user states
user_state = {}

# ---------------- START ----------------
@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text(
        "🤖 PRO Rename Bot Ready!\n\n"
        "📁 Send a file to start."
    )

# ---------------- FILE RECEIVER ----------------
@app.on_message(filters.document | filters.video | filters.audio)
def get_file(_, message: Message):

    user_id = message.from_user.id

    user_state[user_id] = {
        "file": message,
        "step": "choose"
    }

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏ Rename", callback_data="rename"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]
    ])

    message.reply_text(
        "📁 File received!\n\nChoose option:",
        reply_markup=buttons
    )

# ---------------- BUTTON HANDLER ----------------
@app.on_callback_query()
def callback(_, query: CallbackQuery):

    user_id = query.from_user.id

    if query.data == "cancel":
        user_state.pop(user_id, None)
        query.message.edit_text("❌ Cancelled")
        return

    if query.data == "rename":
        if user_id not in user_state:
            query.message.edit_text("❌ No file found")
            return

        user_state[user_id]["step"] = "rename"

        query.message.edit_text(
            "✏ Send new file name (without extension)"
        )

# ---------------- TEXT HANDLER ----------------
@app.on_message(filters.text & ~filters.command("start"))
def rename_handler(_, message: Message):

    user_id = message.from_user.id

    if user_id not in user_state:
        return

    if user_state[user_id]["step"] != "rename":
        return

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
        caption="✅ Renamed Successfully!"
    )

    # Cleanup
    os.remove(new_file_path)
    user_state.pop(user_id, None)

app.run()
