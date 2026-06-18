import os

def get_env(name, default=None, required=True):
    value = os.getenv(name, default)
    if required and value is None:
        raise ValueError(f"❌ Missing ENV: {name}")
    return value

API_ID = int(get_env("API_ID"))
API_HASH = get_env("API_HASH")
BOT_TOKEN = get_env("BOT_TOKEN")
MONGO_URL = get_env("MONGO_URL")

# ===== SPEED SETTINGS =====
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 50))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024 * 1024 * 2))  # 2MB chunks

# ===== BOT SETTINGS =====
DEFAULT_THUMB = "default.jpg"
