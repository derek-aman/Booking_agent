from agents.state import State
from agents.llm_config import llm  
from agents.tools import (
    book_appointment, 
    reschedule_appointment, cancel_appointment, general_query, check_availability,list_doctors,query_database
)
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.mongodb import MongoDBSaver

from langgraph.prebuilt import ToolNode, tools_condition

tools = [
    book_appointment,
    reschedule_appointment,
    check_availability,
    cancel_appointment,
    general_query,
    list_doctors,
    query_database,
]

llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}

def build_graph():
    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools=tools))
    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", tools_condition)
    builder.add_edge("tools", "chatbot")
    return builder

def complie_graph_with_checkpointer(checkpointer):
    return build_graph().compile(checkpointer=checkpointer)

SYSTEM_PROMPT = """
You are a clinic assistant with full database access.
You have access to tools for booking, rescheduling, canceling appointments, checking availability, answering general queries, and listing doctors.
You can search any collection by name (e.g., 'doctor_availability', 'appointment').
If the user does not specify a collection, choose the most relevant one.
Always try a database search before saying something is unavailable.
Be detailed, accurate, and concise.
"""

def run_graph(user_input: str):
    import os
    from dotenv import load_dotenv
    load_dotenv()

    DB_URI = os.getenv("MONGO_URI")
    if not DB_URI:
        raise ValueError("❌ MONGO_URI not set.")

    config = {"configurable": {"thread_id": "10"}}
    with MongoDBSaver.from_conn_string(DB_URI) as mongo_checkpointer:
        graph_with_mongo = complie_graph_with_checkpointer(mongo_checkpointer)
        
        state = State(
            messages=[
                { "role": "system", "content": SYSTEM_PROMPT },
                { "role": "user", "content": user_input }],
            thread_id="10"
        )

        reply = None
        for event in graph_with_mongo.stream(state, config=config, stream_mode='values'):
            if "messages" in event:
                reply = event["messages"][-1]

        return reply.content if reply else "❌ No reply from model."
