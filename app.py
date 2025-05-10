import os
import sys
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from src.load_data import load_all_csvs_to_sqlite, get_all_tables_info, debug_database
from src.sql_agent import SQLQueryAgent
from src.jira_agent import JiraQueryAgent
from src.whatsapp_agent import WhatsAppAgent

# Load environment variables
load_dotenv()

# Constants
DB_PATH = "datasets.db"
DATA_FOLDER = "data"

def setup_database():
    """Set up the database with all CSV files from the data folder"""
    try:
        tables_info = load_all_csvs_to_sqlite(DATA_FOLDER, DB_PATH)
        if tables_info:
            st.success(f"Successfully loaded {len(tables_info)} datasets into the database.")
            
            # Debug database structure after loading
            debug_database(DB_PATH)
            
            return True
        else:
            st.warning("No CSV files found in the data folder. Please add CSV files to the 'data' directory.")
            return False
    except Exception as e:
        st.error(f"Error setting up database: {str(e)}")
        return False

def init_agent():
    """Initialize the SQL agent"""
    # Get info about all tables
    tables_info = get_all_tables_info(DB_PATH)
    
    if 'GOOGLE_API_KEY' not in st.session_state:
        st.session_state.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    api_key = st.session_state.GOOGLE_API_KEY
    
    if not api_key:
        api_key = st.text_input("Enter your Google API Key:", type="password")
        if api_key:
            st.session_state.GOOGLE_API_KEY = api_key
    
    if api_key:
        agent = SQLQueryAgent(api_key, DB_PATH, tables_info)
        return agent
    else:
        return None

def init_jira_agent():
    """Initialize the Jira agent with stored credentials"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        # This will be handled in the main function when initializing SQL agent
        return None
    
    # Get Jira settings from session state only (not from environment variables)
    jira_config = {
        "username": st.session_state.get("jira_username", ""),
        "api_token": st.session_state.get("jira_api_token", ""),
        "instance_url": st.session_state.get("jira_instance_url", ""),
        "is_cloud": st.session_state.get("jira_is_cloud", True)
    }
    
    # Check if we have minimum required credentials
    if not jira_config["instance_url"] or not jira_config["api_token"] or not jira_config["username"]:
        return None
    
    # Create the Jira agent
    return JiraQueryAgent(api_key, jira_config)

def init_whatsapp_agent():
    """Initialize the WhatsApp agent with stored credentials"""
    account_sid = st.session_state.get("twilio_account_sid", "")
    auth_token = st.session_state.get("twilio_auth_token", "")
    from_number = st.session_state.get("twilio_whatsapp_number", "")
    
    if not account_sid or not auth_token or not from_number:
        return None
    
    return WhatsAppAgent(account_sid, auth_token, from_number)

def jira_settings():
    """UI for Jira settings configuration"""
    st.subheader("Jira Connection Settings")
    
    # Initialize session state for Jira settings (with empty defaults, not from env)
    if "jira_username" not in st.session_state:
        st.session_state.jira_username = ""
    if "jira_api_token" not in st.session_state:
        st.session_state.jira_api_token = ""
    if "jira_instance_url" not in st.session_state:
        st.session_state.jira_instance_url = ""
    if "jira_is_cloud" not in st.session_state:
        st.session_state.jira_is_cloud = True

    # Jira instance URL
    st.session_state.jira_instance_url = st.text_input(
        "Jira Instance URL (e.g., https://yourcompany.atlassian.net)", 
        value=st.session_state.jira_instance_url
    )
    
    # Username and API Token
    st.session_state.jira_username = st.text_input("Jira Username (Email)", value=st.session_state.jira_username)
    st.session_state.jira_api_token = st.text_input("Jira API Token", type="password", value=st.session_state.jira_api_token)
    
    # Cloud or Server
    st.session_state.jira_is_cloud = st.checkbox("Is Jira Cloud?", value=st.session_state.jira_is_cloud)
    
    # Test connection button
    if st.button("Test Jira Connection"):
        with st.spinner("Testing connection to Jira..."):
            agent = init_jira_agent()
            if agent and agent.is_initialized():
                result = agent.verify_connection()
                if result["status"] == "success":
                    st.success(result["message"])
                    if result.get("projects"):
                        st.write("Sample projects: " + ", ".join(result["projects"]))
                else:
                    st.error(result["message"])
            else:
                st.error("Failed to initialize Jira connection. Please check your credentials.")

    # Provide instructions for getting API token - without using an expander
    st.markdown("##### How to get your Jira API token")
    st.markdown("""
    1. Log in to [Atlassian account management](https://id.atlassian.com/manage/api-tokens)
    2. Click "Create API token"
    3. Give your token a name (e.g., "Fortune 1000 RAG App")
    4. Copy the generated token and paste it in the field above
    """)
    
    st.markdown("---")
    
    st.subheader("Jira Assistant")
    
    agent = init_jira_agent()
    
    if agent and agent.is_initialized():
        st.write("You can ask questions about your Jira projects, issues, or perform tasks:")
        
        st.markdown("""
        **Example commands:**
        - Create a new bug in project PROJ with summary "Login page crashes on mobile devices" and priority High
        - Assign ticket PROJ-123 to John Smith
        - Update the status of PROJ-456 to "In Progress"
        - Show all blockers in the current sprint for project MARKETING
        - List all issues assigned to me that are due this week
        """)
        
        jira_query = st.text_area("Ask a question about Jira:", height=80)
        
        if st.button("Submit Jira Query"):
            if jira_query:
                with st.spinner("Processing your Jira query..."):
                    try:
                        response = agent.query(jira_query)
                        st.write("### Response")
                        st.markdown(response)
                    except Exception as e:
                        st.error(f"Error processing your query: {str(e)}")
            else:
                st.warning("Please enter a question about Jira.")
    else:
        st.info("Complete your Jira connection setup above to use the Jira Assistant.")

def whatsapp_settings():
    """UI for WhatsApp settings configuration"""
    st.subheader("WhatsApp Integration Settings")
    
    # Initialize session state for WhatsApp settings
    if "twilio_account_sid" not in st.session_state:
        st.session_state.twilio_account_sid = ""
    if "twilio_auth_token" not in st.session_state:
        st.session_state.twilio_auth_token = ""
    if "twilio_whatsapp_number" not in st.session_state:
        st.session_state.twilio_whatsapp_number = ""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.twilio_account_sid = st.text_input(
            "Twilio Account SID", 
            value=st.session_state.twilio_account_sid
        )
    
    with col2:
        st.session_state.twilio_auth_token = st.text_input(
            "Twilio Auth Token", 
            type="password", 
            value=st.session_state.twilio_auth_token
        )
    
    st.session_state.twilio_whatsapp_number = st.text_input(
        "WhatsApp Number (with country code, e.g., +14155238886)", 
        value=st.session_state.twilio_whatsapp_number
    )
    
    # Test connection button
    if st.button("Test Twilio Connection"):
        with st.spinner("Testing connection to Twilio..."):
            agent = init_whatsapp_agent()
            if agent and agent.is_initialized():
                result = agent.verify_connection()
                if result["status"] == "success":
                    st.success(result["message"])
                else:
                    st.error(result["message"])
            else:
                st.error("Failed to initialize WhatsApp connection. Please check your credentials.")
    
    # Display webhook URL for configuration
    st.markdown("---")
    st.subheader("Webhook Setup Instructions")
    st.markdown("""
    To receive WhatsApp messages, you need to configure a webhook in your Twilio dashboard:
    
    1. Deploy this application somewhere publicly accessible (Heroku, AWS, etc.)
    2. Set your Twilio WhatsApp webhook URL to:
       `https://your-app-url.com/webhook`
    3. Make sure the webhook is configured to send HTTP POST requests
    
    For local development, you can use tools like ngrok:
    ```
    ngrok http 5001
    ```
    Then use the ngrok URL + `/webhook` as your webhook URL in the Twilio dashboard.
    """)
    
    st.markdown("---")
    
    # WhatsApp messaging interface
    st.subheader("Send WhatsApp Message")
    
    agent = init_whatsapp_agent()
    
    if agent and agent.is_initialized():
        # Get all tables information to display datasets
        try:
            tables_info = get_all_tables_info(DB_PATH)
            dataset_names = [table['name'].replace('_', ' ').title() for table in tables_info]
            
            # Display available datasets
            with st.expander("Available datasets for queries", expanded=False):
                for name in dataset_names:
                    st.write(f"- {name}")
        except:
            pass
            
        col1, col2 = st.columns([2, 1])
        
        with col1:
            message = st.text_area("Message to send:", height=100)
        
        with col2:
            to_number = st.text_input(
                "Recipient's WhatsApp number (with country code, e.g., +1234567890):"
            )
        
        # Send button
        if st.button("Send WhatsApp Message"):
            if message and to_number:
                with st.spinner("Sending message..."):
                    result = agent.send_message(to_number, message)
                    if result["status"] == "success":
                        st.success(f"Message sent successfully! {result.get('details', '')}")
                    else:
                        st.error(result["message"])
            else:
                st.warning("Please enter both a message and a recipient number.")
    else:
        st.info("Complete your WhatsApp configuration above to use the messaging feature.")

def main():
    st.set_page_config(page_title="Dataset SQL Assistant", layout="wide")
    
    st.title("Dataset SQL Assistant")
    st.sidebar.title("Options")

    if st.sidebar.button("Debug Database"):
        debug_database(DB_PATH)

    has_data = setup_database()
    
    if has_data:
        agent = init_agent()
    else:
        agent = None
    
    tab1, tab2, tab3 = st.tabs(["Query Datasets", "Jira Settings", "WhatsApp Integration"])
    
    with tab1:
        if has_data and agent:
            st.header("Ask questions about your datasets")
            
            tables_info = get_all_tables_info(DB_PATH)
            dataset_names = [table['name'].replace('_', ' ').title() for table in tables_info]
            
            st.write("Available datasets:")
            for name in dataset_names:
                st.write(f"- {name}")
            
            query = st.text_area("Ask a question about your data:", height=80)
            if st.button("Submit"):
                if query:
                    with st.spinner("Generating response..."):
                        result = agent.query(query)
                        st.write("### Answer")
                        st.write(result["answer"])
                        
                        with st.expander("SQL Query Used"):
                            st.code(result["sql_query"], language="sql")
                        
                        if "data" in result and result["data"] is not None and not result["data"].empty:
                            st.write("### Data")
                            st.dataframe(result["data"])
                else:
                    st.warning("Please enter a question.")
        else:
            if not has_data:
                st.info("Please add CSV files to the 'data' directory to get started.")
            else:
                st.info("Please enter your Google API key in the sidebar to enable the assistant.")
    
    with tab2:
        jira_settings()
        
    with tab3:
        whatsapp_settings()

if __name__ == "__main__":
    main()
