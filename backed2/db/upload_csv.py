import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB connection details from .env
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "PatientData")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION", "appointments")  # Upload to same collection used by your app

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is missing in .env")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Path to CSV file
CSV_FILE = r"C:\Users\Aman Kumar\Desktop\AI_Agent\backed2\doctor_availability.csv"

if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(f"❌ CSV file not found at: {CSV_FILE}")

# Read the CSV
df = pd.read_csv(CSV_FILE)

# Replace NaN with None for MongoDB
df = df.where(pd.notnull(df), None)

# Convert to list of dictionaries
data = df.to_dict(orient="records")

if not data:
    print("❌ No data found in CSV.")
else:
    # Optional: clear old data before inserting
    deleted_count = collection.delete_many({}).deleted_count
    print(f"🗑 Cleared {deleted_count} existing records from '{COLLECTION_NAME}'.")

    # Insert into MongoDB
    result = collection.insert_many(data)
    print(f"✅ Inserted {len(result.inserted_ids)} documents into '{COLLECTION_NAME}' collection.")
