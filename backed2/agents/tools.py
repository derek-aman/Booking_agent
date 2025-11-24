from langchain_core.tools import tool

from langchain_core.messages import HumanMessage
from agents.llm_config import llm  
import re
from db.crud import create_appointment, get_appointments, update_appointment, delete_appointment,get_all_doctors

@tool
def book_appointment(patient_name: str, doctor_name: str, date: str, time: str):
    """Book a new appointment"""
    data = {
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "date": date,
        "time": time,
        "status": "booked"
    }
    appointment_id = create_appointment(data)
    return {"success": True, "appointment_id": str(appointment_id)}

@tool
def check_availability(doctor_name: str, date: str):
    """Check if a doctor has an appointment on a given date"""
    appointments = get_appointments({"doctor_name": doctor_name, "date": date})
    if appointments:
        return {"available": False, "appointments": appointments}
    return {"available": True}

@tool
def reschedule_appointment(patient_name: str, doctor_name: str, old_date: str, old_time: str, new_date: str, new_time: str):
    """Reschedule an appointment"""
    result = update_appointment(
        {"patient_name": patient_name, "doctor_name": doctor_name, "date": old_date, "time": old_time},
        {"date": new_date, "time": new_time}
    )
    if result.modified_count > 0:
        return {"success": True}
    return {"success": False, "message": "No matching appointment to reschedule"}

@tool
def cancel_appointment(patient_name: str, doctor_name: str, date: str, time: str):
    """Cancel an existing appointment"""
    result = delete_appointment({
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "date": date,
        "time": time
    })
    if result.deleted_count > 0:
        return {"success": True}
    return {"success": False, "message": "No matching appointment found"}

@tool
def general_query(query: str) -> str:
    """Responds to general queries like 
     "working hours": "Our doctors are available from 9 AM to 6 PM.",
        "contact": "You can call us at +91 12345 67890", '."""
    try:
        response = llm.invoke([HumanMessage(content=query)])
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"
    
@tool
def list_doctors(specialization: str = None):
    """List all doctors, or doctors of a specific specialization"""
    doctors = get_all_doctors(specialization)
    if not doctors:
        if specialization:
            return {"success": False, "message": f"No doctors found for specialization: {specialization}"}
        return {"success": False, "message": "No doctors found in the database."}
    
    return {"success": True, "doctors": doctors}


@tool("query_database", return_direct=True)
def query_database(collection_name: str, search_text: str = "") -> str:
    """
    Queries any MongoDB collection in the connected database.

    Args:
        collection_name (str): The MongoDB collection name (e.g., 'doctor_availability', 'appointment').
        search_text (str, optional): Text to search for in any field (case-insensitive). 
                                     If empty, returns all records.

    Returns:
        str: Formatted list of matching records, or a message if none found.
    """
    # Check collection exists
    if collection_name not in db.list_collection_names():
        return f"❌ Collection '{collection_name}' does not exist in database."

    collection = db[collection_name]

    # Build query
    query = {}
    if search_text.strip():
        regex = re.compile(search_text.strip(), re.IGNORECASE)
        query = {
            "$or": [
                {field: regex} for field in collection.find_one().keys() if field != "_id"
            ]
        }

    # Fetch results
    results = list(collection.find(query, {"_id": 0}))

    if not results:
        return f"❌ No records found for search: '{search_text}' in '{collection_name}'."

    # Format results for display
    formatted = []
    for idx, r in enumerate(results, 1):
        formatted.append(f"{idx}. " + " | ".join(f"{k}: {v}" for k, v in r.items()))

    return "\n".join(formatted)
