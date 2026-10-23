import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).with_name(".env"))

client = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=5000)
db = client["fishapi"]
posts = db["posts"]