import streamlit as st
import time
from agents.graph import run_graph


st.title('Appointment Booking AI Agent')

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Show chat history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Get new user input
user_input = st.chat_input("Type here")

if user_input:
    # Append user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_graph(user_input)

            # Typing effect simulation
            placeholder = st.empty()
            typed_text = ""
            for char in response:
                typed_text += char
                placeholder.markdown(typed_text)
                time.sleep(0.015)  # typing delay

            st.session_state['message_history'].append({'role': 'assistant', 'content': response})
