from pymongo import MongoClient
from config import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["telegram_bot"]

users = db["users"]

def add_user(user_id):
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "premium": False,
            "files": 0
        })

def get_user(user_id):
    return users.find_one({"user_id": user_id})
