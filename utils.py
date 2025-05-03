import streamlit as st
import json
import os
import datetime

def load_pipelines():
    """Load pipeline data from file"""
    if os.path.exists("pipelines.json"):
        with open("pipelines.json", "r") as f:
            return json.load(f)
    return {}

def save_pipelines(pipelines):
    """Save pipeline data to file"""
    with open("pipelines.json", "w") as f:
        json.dump(pipelines, f)

def encrypt_credentials(value):
    """Simple encryption for credentials (in a real app, use proper encryption)"""
    # This is a placeholder - in a real application, use proper encryption
    return value

def decrypt_credentials(value):
    """Simple decryption for credentials (in a real app, use proper decryption)"""
    # This is a placeholder - in a real application, use proper decryption
    return value

def generate_chat_response(user_input, context=None):
    """
    Generate a response to the user's input
    In a real app, this would integrate with an actual AI model or API
    """
    # This is a placeholder for a real chatbot response system
    if "pipeline" in user_input.lower():
        return "I can help you with your data pipelines. Would you like to create a new pipeline or view existing ones?"
    elif "create" in user_input.lower():
        return "To create a new pipeline, navigate to the 'My Pipelines' section and use the 'Create New Pipeline' form."
    elif "help" in user_input.lower():
        return """
        I can help you with:
        - Managing your data pipelines
        - Setting up new data connections
        - Providing information about your datasets
        - Explaining how to use this application
        
        What would you like to know more about?
        """
    else:
        return f"I understand you're asking about: '{user_input}'. How can I assist you with this?"

def format_timestamp(timestamp=None):
    """Format timestamp for chat history display"""
    if timestamp is None:
        timestamp = datetime.datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M")

def initialize_session_state():
    """Initialize all required session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    
    if "pipelines" not in st.session_state:
        st.session_state.pipelines = load_pipelines()
        
        # If no pipelines exist, create sample data
        if not st.session_state.pipelines:
            st.session_state.pipelines = {
                "pipeline1": {
                    "name": "Sales Data ETL",
                    "description": "Extract, transform, and load sales data from multiple sources",
                    "dataset": "Sales transactions 2020-2025",
                    "storage": {
                        "type": "Data Warehouse",
                        "name": "Snowflake",
                        "api_key": encrypt_credentials("YOUR_API_KEY_HERE"),
                        "password": encrypt_credentials("YOUR_PASSWORD_HERE")
                    }
                }
            }
    
    if "page" not in st.session_state:
        st.session_state.page = "chat"  # Default page