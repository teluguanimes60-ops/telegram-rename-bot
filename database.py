# ===== ADVANCED DATABASE SYSTEM (MongoDB) =====

from pymongo import MongoClient
from config import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["AniToonsBot"]

users = db["users"]

# ===== ADD USER =====
def add_user(user_id):
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "saved_name": None,
            "thumb": None,
            "files": 0,
            "joined": True,
            "created_at": str(user_id)
        })

# ===== GET USER =====
def get_user(user_id):
    user = users.find_one({"user_id": user_id})
    if not user:
        add_user(user_id)
        user = users.find_one({"user_id": user_id})
    return user

# ===== UPDATE FIELD =====
def set_user(user_id, key, value):
    users.update_one(
        {"user_id": user_id},
        {"$set": {key: value}},
        upsert=True
    )

# ===== INCREMENT FILE COUNT =====
def add_file_count(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"files": 1}},
        upsert=True
    )

# ===== DELETE USER (OPTIONAL) =====
def delete_user(user_id):
    users.delete_one({"user_id": user_id})

# ===== GET ALL USERS (ADMIN USE) =====
def all_users():
    return users.find()

# ===== STATS =====
def total_users():
    return users.count_documents({})
