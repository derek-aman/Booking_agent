import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGODB_DB", "PatientData")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is missing in .env")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)

db = client[DB_NAME]

appointments_collection = db[os.getenv("MONGODB_COLLECTION", "appointments")]
