from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
mongo_uri = os.getenv("MONGO_URL")
client = MongoClient(mongo_uri)
db = client["PatientData"]

# Use the appointments collection
appointments_collection = db["appointments"]

# CRUD Operations

def create_appointment(data):
    return appointments_collection.insert_one(data).inserted_id

def get_appointments(query={}):
    return list(appointments_collection.find(query))

def update_appointment(query, update):
    return appointments_collection.update_one(query, {'$set': update})

def delete_appointment(query):
    return appointments_collection.delete_one(query)
