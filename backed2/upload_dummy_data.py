# upload_dummy_data.py

import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "PatientData")
COLLECTION_NAME = os.getenv("MONGODB_COLLECTION", "appointment")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Read CSV
csv_path = "doctor_availability.csv"  # It's already in your root folder
df = pd.read_csv(csv_path)

# Optional: Avoid inserting duplicates (by doctor_name)
existing_doctors = collection.distinct("doctor_name")
filtered_df = df[~df["doctor_name"].isin(existing_doctors)]

if filtered_df.empty:
    print("✅ No new records to insert. All doctor names already exist.")
else:
    records = filtered_df.to_dict(orient="records")
    result = collection.insert_many(records)
    print(f"✅ Inserted {len(result.inserted_ids)} new records.")
