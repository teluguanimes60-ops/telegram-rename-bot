from pymongo import MongoClient
from config import MONGO_URL
import time

client = MongoClient(MONGO_URL)
db = client["anitools_bot"]

users = db["users"]
stats = db["stats"]

# ===== CACHE SYSTEM (FASTER) =====
USER_CACHE = {}

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
    if user_id in USER_CACHE:
        return USER_CACHE[user_id]

    user = users.find_one({"user_id": user_id}) or {}
    USER_CACHE[user_id] = user
    return user

def set_user(user_id, key, value):
    users.update_one(
        {"user_id": user_id},
        {"$set": {key: value}},
        upsert=True
    )
    if user_id in USER_CACHE:
        USER_CACHE[user_id][key] = value

# ===== PREMIUM =====
def set_premium(user_id, status=True):
    set_user(user_id, "premium", status)

def is_premium(user_id):
    return get_user(user_id).get("premium", False)

# ===== FILE COUNT =====
def increase_files(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"files": 1}},
        upsert=True
    )

def get_file_count(user_id):
    return get_user(user_id).get("files", 0)

# ===== THUMB =====
def set_thumbnail(user_id, path):
    set_user(user_id, "thumb", path)

def get_thumbnail(user_id):
    return get_user(user_id).get("thumb")

# ===== SAVED NAME =====
def set_saved_name(user_id, name):
    set_user(user_id, "saved_name", name)

def get_saved_name(user_id):
    return get_user(user_id).get("saved_name")

# ===== STATS =====
def add_task():
    stats.update_one(
        {"id": "global"},
        {"$inc": {"tasks": 1}},
        upsert=True
    )

def get_stats():
    return stats.find_one({"id": "global"}) or {"tasks": 0}

# ===== ADMIN =====
def get_total_users():
    return users.count_documents({})

def get_all_users():
    return list(users.find({}, {"_id": 0}))
