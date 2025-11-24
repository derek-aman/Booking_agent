from typing_extensions import TypedDict
import os
import uuid
import pandas as pd
from model import *
from dotenv import load_dotenv
from typing import Annotated, Literal
import pandas as pd
import re
from datetime import datetime
from langchain.tools import tool 
import asyncio
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
    

load_dotenv()



class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str



# Doctor list constant
DOCTOR_LIST = Literal[
    'kevin anderson', 'robert martinez', 'susan davis', 'daniel miller', 'sarah wilson',
    'michael green', 'lisa brown', 'jane smith', 'emily johnson', 'john doe'
]

# ---------------- TOOLS ---------------- #

@tool
def check_availability_by_doctor(desired_date: DateModel, doctor_name: DOCTOR_LIST):
    """
    Check availability for a specific doctor on a specific date.
    """
    df = pd.read_csv(r"doctor_availability.csv")
    # df['date_slot_time'] = df['date_slot'].apply(lambda input: input.split(' ')[-1])

    rows = list(df[
        (df['date_slot'].apply(lambda input: input.split(' ')[0]) == desired_date.date) &
        (df['doctor_name'] == doctor_name) &
        (df['is_available'] == True)
    ]['date_slot_time'])

    if not rows:
        return "No availability in the entire day"
    return f'Availability for {desired_date.date}\nAvailable slots: ' + ', '.join(rows)


 # Assuming you're using LangChain tool decorator

@tool
def check_availability_by_specialization(desired_date: str, specialization: str):
    """
    Check availability for a specialization on a specific date (flexible input).
    """
    df = pd.read_csv("doctor_availability.csv")
    df['date_slot_time'] = df['date_slot'].apply(lambda input: input.split(' ')[-1])

    # Normalize date input to DD-MM-YYYY if needed
    try:
        date_obj = datetime.strptime(desired_date.strip(), "%d-%m-%Y")
        desired_date = date_obj.strftime("%d-%m-%Y")
    except:
        pass

    rows = df[
        (df['date_slot'].apply(lambda input: input.split(' ')[0]) == desired_date) &
        (df['specialization'].str.lower() == specialization.lower()) &
        (df['is_available'] == True)
    ].groupby(['specialization', 'doctor_name'])['date_slot_time'].apply(list).reset_index(name='available_slots')

    if len(rows) == 0:
        return f"No availability for {specialization} on {desired_date}."

    def convert_to_am_pm(time_str):
        hours, minutes = map(int, str(time_str).split(":"))
        period = "AM" if hours < 12 else "PM"
        hours = hours % 12 or 12
        return f"{hours}:{minutes:02d} {period}"

    output = f"Availability for {desired_date}\n"
    for row in rows.values:
        output += f"{row[1]} - Available slots: \n" + ', \n'.join([convert_to_am_pm(value) for value in row[2]]) + '\n'
    return output


@tool
def set_appointment(desired_date: str, doctor_name: str):
    """
    Book an appointment for the given date and doctor.
    Accepts just 'DD-MM-YYYY' or 'DD-MM-YYYY HH:MM'.
    If only date is given, picks the first available slot.
    """
    df = pd.read_csv("doctor_availability.csv")
    date_input = desired_date.strip()

    # If only date provided
    if re.match(r"^\d{2}-\d{2}-\d{4}$", date_input):
        case = df[(df['doctor_name'].str.lower() == doctor_name.lower()) &
                  (df['is_available'] == True) &
                  (df['date_slot'].str.startswith(date_input))]
        if case.empty:
            return f"❌ No available slots for {doctor_name} on {date_input}."
        slot = case.iloc[0]['date_slot']
        desired_date = slot
    else:
        try:
            datetime.strptime(date_input, "%d-%m-%Y %H:%M")
            slot = datetime.strptime(date_input, "%d-%m-%Y %H:%M").strftime("%d-%m-%Y %#H.%M")
        except:
            return "❌ Invalid date format. Please use 'DD-MM-YYYY' or 'DD-MM-YYYY HH:MM'."

    # Check availability
    case = df[(df['date_slot'].str.startswith(desired_date[:16])) &
              (df['doctor_name'].str.lower() == doctor_name.lower()) &
              (df['is_available'] == True)]

    if case.empty:
        return f"❌ Slot with {doctor_name} at {desired_date} is already booked or unavailable."

    df.loc[(df['date_slot'].str.startswith(desired_date[:16])) &
           (df['doctor_name'].str.lower() == doctor_name.lower()),
           ['is_available']] = [False]
    df.to_csv("doctor_availability.csv", index=False)

    return f"✅ Appointment confirmed with {doctor_name} on {desired_date}."


@tool
def confirm_appointment(desired_date: str, doctor_name: str):
    """
    Confirms an appointment if available.
    """
    df = pd.read_csv("doctor_availability.csv")

    
    df.to_csv("doctor_availability.csv", index=False)

    return f"✅ Appointment confirmed with {doctor_name} on {desired_date}."


@tool
def general_query(query: str) -> str:
    """Responds to any kind of general query like 'What is AI?', 'Tell me a joke', or 'Summarize a paragraph'."""
    try:
        response = llm.invoke([HumanMessage(content=query)])
        return response.content
    except Exception as e:
        return f"Error while processing your query: {str(e)}"


@tool
def reschedule_appointment(old_date: str, new_date: str, doctor_name: str):
    """
    Reschedule an appointment.
    """
    

    return set_appointment(new_date, doctor_name)



# ---------------- STATE & GRAPH ---------------- #

tools = [check_availability_by_doctor, check_availability_by_specialization,
         set_appointment, reschedule_appointment, confirm_appointment, general_query]





llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ["GOOGLE_API_KEY"]
)

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}


tool_node = ToolNode(tools=tools)

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile()




def complie_graph_with_checkpointer(checkpointer):
    graph_with_checkpointer = graph_builder.compile(checkpointer=checkpointer)
    return graph_with_checkpointer






# def main():
#     # DB_URI = "mongodb://<username>11;<password>@<host>:<port>"
#     DB_URI = os.getenv("MONGO_URI")

#     if not DB_URI:
#         raise ValueError("❌ MONGODB_URI is not set in your .env file.")
#     config = {"configurable": {"thread_id": "5"}} 
    
#     with MongoDBSaver.from_conn_string(DB_URI) as mongo_checkpointer:
#         graph__with_mongo = complie_graph_with_checkpointer(mongo_checkpointer)
#         while True:
#           user_query = input("> ")
#         # initial state
#           state = State(
#             messages=[{ "role": "user", "content": user_query}],
#             thread_id="5"
#           )

#           for event in graph__with_mongo.stream(state, config=config, stream_mode="values"):
#             if "messages" in event:
#                 reply = event["messages"][-1]

#           return reply.content if reply else "No reply"


# main()


# graph.py
def run_graph(user_input: str):
    DB_URI = os.getenv("MONGO_URI")
    if not DB_URI:
        raise ValueError("❌ MONGO_URI is not set in your .env file.")

    config = {"configurable": {"thread_id": "5"}}
    with MongoDBSaver.from_conn_string(DB_URI) as mongo_checkpointer:
        graph_with_mongo = complie_graph_with_checkpointer(mongo_checkpointer)
        
        state = State(
            messages=[{ "role": "user", "content": user_input }],
            thread_id="5"
        )

        reply = None
        for event in graph_with_mongo.stream(state, config=config, stream_mode='values'):
            if "messages" in event:
                reply = event["messages"][-1]

        return reply.content if reply else "❌ No reply from model."




