from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("start"))
def start(client, message):

    text = """
🔥 **AniToons Rename Bot - ULTRA PRO MAX**

🚀 Features:
• ⚡ Ultra Fast Rename Engine  
• 🎬 Video Tools (Convert + Info + Screenshot)  
• 🖼 Auto Thumbnail Generator  
• 📦 Batch + Smart Rename  
• 🎯 Netflix Style Naming  
• 💎 Premium Speed System  

📌 Send a file or choose option below 👇
"""

buttons = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📁 Rename", callback_data="rename"),
        InlineKeyboardButton("🎬 Convert", callback_data="convert")
    ],
    [
        InlineKeyboardButton("⚙ Settings", callback_data="settings"),
        InlineKeyboardButton("📊 Status", callback_data="status")
    ],
    [
        InlineKeyboardButton("🔙 Back", callback_data="back")
    ]
])
    message.reply_text(text, reply_markup=buttons)
