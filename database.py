# ===== AniToons Database (PRO VERSION) =====

from pymongo import MongoClient
from config import MONGO_URL
import time

# ===== CONNECT =====
client = MongoClient(MONGO_URL)
db = client["anitools_bot"]

users = db["users"]
stats = db["stats"]

# ===== USER SYSTEM =====

def add_user(user_id):
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "saved_name": None,
            "thumb": None,
            "premium": False,
            "files": 0,
            "joined": int(time.time())
        })

def get_user(user_id):
    user = users.find_one({"user_id": user_id})
    return user if user else {}

def set_user(user_id, key, value):
    users.update_one(
        {"user_id": user_id},
        {"$set": {key: value}},
        upsert=True
    )

# ===== PREMIUM SYSTEM =====

def set_premium(user_id, status=True):
    users.update_one(
        {"user_id": user_id},
        {"$set": {"premium": status}},
        upsert=True
    )

def is_premium(user_id):
    user = get_user(user_id)
    return user.get("premium", False)

# ===== FILE COUNT =====

def increase_files(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"files": 1}},
        upsert=True
    )

def get_file_count(user_id):
    user = get_user(user_id)
    return user.get("files", 0)

# ===== THUMBNAIL =====

def set_thumbnail(user_id, path):
    set_user(user_id, "thumb", path)

def get_thumbnail(user_id):
    user = get_user(user_id)
    return user.get("thumb")

# ===== SAVED NAME =====

def set_saved_name(user_id, name):
    set_user(user_id, "saved_name", name)

def get_saved_name(user_id):
    user = get_user(user_id)
    return user.get("saved_name")

# ===== GLOBAL STATS =====

def add_task():
    stats.update_one(
        {"id": "global"},
        {"$inc": {"tasks": 1}},
        upsert=True
    )

def get_stats():
    s = stats.find_one({"id": "global"})
    return s if s else {"tasks": 0}

# ===== ADMIN HELP =====

def get_total_users():
    return users.count_documents({})

def get_all_users():
    return list(users.find({}, {"_id": 0}))
