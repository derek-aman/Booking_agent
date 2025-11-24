# db/crud.py
from db.connection import appointments_collection

def create_appointment(data: dict):
    """Create a new appointment"""
    return appointments_collection.insert_one(data).inserted_id

def get_appointments(query: dict = {}):
    """Get appointments matching query"""
    return list(appointments_collection.find(query))

def update_appointment(query: dict, update: dict):
    """Update appointment(s)"""
    result = appointments_collection.update_one(query, {"$set": update})
    return {"matched": result.matched_count, "modified": result.modified_count}

def delete_appointment(query: dict):
    """Delete appointment(s)"""
    result = appointments_collection.delete_one(query)
    return {"deleted": result.deleted_count}

def get_all_doctors(specialization: str = None):
    """Return all doctors, or only those with a specific specialization"""
    query = {}
    if specialization:
        query["specialization"] = specialization
    return list(appointments_collection.find(query, {"_id": 0, "name": 1, "specialization": 1}))
