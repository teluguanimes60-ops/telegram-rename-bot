from pyrogram import Client, filters
from config import *
from flask import Flask
import threading

# Flask app (fake web server)
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    web_app.run(host="0.0.0.0", port=10000)

# Telegram bot
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
def start(_, message):
    message.reply_text("🤖 Bot is Alive!")

# Run both
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app.run()
