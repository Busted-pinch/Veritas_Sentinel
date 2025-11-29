# backend/app/db/mongo.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # loads variables from .env

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)
db = client["fraud_ai"]

users_col = db["users"]
txns_col = db["transactions"]
profiles_col = db["user_profiles"]
alerts_col = db["alerts"]
logs_col = db["model_logs"]
