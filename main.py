import streamlit as st
import json
import os
from datetime import datetime
import download_report
import call_agent

# Import utility functions
from utils import initialize_session_state, generate_chat_response, save_pipelines, load_pipelines

# Set page configuration
st.set_page_config(
    page_title="Data Pipeline Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
initialize_session_state()

# Functions
def create_new_chat():
    """Create a new chat and set it as current"""
    chat_id = f"chat_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    st.session_state.chat_history[chat_id] = {
        "title": "New Chat",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = []
    
def select_chat(chat_id):
    """Select an existing chat"""
    if chat_id in st.session_state.chat_history:
        st.session_state.current_chat_id = chat_id
        st.session_state.messages = st.session_state.chat_history[chat_id]["messages"]
    else:
        st.error("Chat not found!")

def on_message_submit():
    """Handle message submission from the chat input"""
    if st.session_state.user_input and st.session_state.current_chat_id:
        user_message = st.session_state.user_input
        
        # Add user message to session
        st.session_state.messages.append({"role": "user", "content": user_message})
        
        # Generate bot response
        bot_response = generate_chat_response(user_message)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        # Update chat history
        st.session_state.chat_history[st.session_state.current_chat_id]["messages"] = st.session_state.messages
        
        # Update chat title if this is the first message
        if len(st.session_state.messages) == 2:  # First user message and bot response
            # Use first few words of user's first message as the chat title
            title_preview = user_message[:20] + ("..." if len(user_message) > 20 else "")
            st.session_state.chat_history[st.session_state.current_chat_id]["title"] = title_preview
        
        # Clear input (this will be done automatically since we're using on_submit)

# Sidebar navigation
with st.sidebar:
    st.markdown(
        """
        <style>
        [data-testid="stImage"] {
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            margin-bottom: 20px;
        }
        
        [data-testid="stImage"] > img {
            width: 150px !important;
            max-width: 80% !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Use standard st.image with a container width
    st.image("boxbot_logo.png", use_container_width=False)
    
    # Navigation buttons
    if st.button("New Chat"):
        create_new_chat()
        st.session_state.page = "chat"
    
    if st.button("Call Campaign"):
        st.session_state.page = "call_agent"

    if st.button("Download Report"):
        st.session_state.page = "download_report"
    
    # Chat History section
    st.subheader("Chat History")
    if st.session_state.chat_history:
        for chat_id, chat_data in st.session_state.chat_history.items():
            chat_title = chat_data.get("title", "New Chat")
            timestamp = chat_data.get("timestamp", "")
            
            if st.button(f"{chat_title} ({timestamp})", key=f"select_{chat_id}"):
                select_chat(chat_id)
                st.session_state.page = "chat"
    else:
        st.write("No chat history yet. Start a new chat!")

# Main content area based on selected page

if st.session_state.page == "chat":
    # Initialize chat if needed
    if st.session_state.current_chat_id is None:
        create_new_chat()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


    # Chat input - using on_submit callback
    user_input = st.chat_input("Type your message here...", key="user_input", on_submit=on_message_submit)

elif st.session_state.page == "download_report":
        download_report.download_report()

elif st.session_state.page == "call_agent":
    call_agent.call_agent_page()

# Save state on each run
save_pipelines(st.session_state.pipelines)