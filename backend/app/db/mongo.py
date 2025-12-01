from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/Veritas_Sentinel")

client = MongoClient(MONGO_URI)
db = client.get_default_database()   # ← THIS selects Veritas_Sentinel automatically

users_col = db["users"]
txns_col = db["transactions"]
profiles_col = db["user_profiles"]
alerts_col = db["alerts"]
logs_col = db["model_logs"]
