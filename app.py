import os
import sys
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from src.load_data import load_csv_to_sqlite, get_table_info
from src.sql_agent import SQLQueryAgent
from src.jira_agent import JiraQueryAgent

# Load environment variables
load_dotenv()

# Constants
DB_PATH = "fortune1000.db"
TABLE_NAME = "fortune1000"
CSV_PATH = "data/fortune1000_2024.csv"

def setup_database():
    """Set up the database if it doesn't exist"""
    if not os.path.exists(DB_PATH):
        try:
            # Load CSV to SQLite
            df, engine = load_csv_to_sqlite(CSV_PATH, DB_PATH, TABLE_NAME)
            st.success("Database created successfully!")
            return True
        except Exception as e:
            st.error(f"Error creating database: {str(e)}")
            return False
    return True

def init_agent():
    """Initialize the SQL agent"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        st.warning("Google API Key not found. Please enter it below:")
        api_key = st.text_input("Google API Key", type="password")
        if not api_key:
            return None
    
    # Get table information to help the agent
    table_info = get_table_info(DB_PATH, TABLE_NAME)
    
    # Create the agent
    return SQLQueryAgent(DB_PATH, api_key, table_info)

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

def main():
    st.set_page_config(
        page_title="Fortune 1000 SQL & Jira Assistant",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Fortune 1000 SQL & Jira Assistant")
    
    # Create tabs for SQL and Jira functionality
    tab1, tab2 = st.tabs(["Fortune 1000 Data", "Jira Integration"])
    
    with tab1:
        st.markdown("""
        Ask questions about the Fortune 1000 companies dataset using natural language.
        This assistant uses LangChain with Gemini to answer your questions by generating SQL queries behind the scenes.
        """)
        
        # Setup database
        db_ready = setup_database()
        if not db_ready:
            st.stop()
        
        # Initialize agent
        agent = init_agent()
        if not agent:
            st.stop()
        
        # Input for user question
        question = st.text_area("Ask a question about Fortune 1000 companies:", 
                            "Which companies in the technology sector have the highest revenue?")
        
        if st.button("Get Answer"):
            if question:
                with st.spinner("Generating answer..."):
                    # Get answer from the agent
                    answer = agent.query(question)
                    st.markdown("### Answer")
                    st.write(answer)
            else:
                st.warning("Please enter a question.")
        
        # Example questions
        st.markdown("### Example Questions")
        examples = [
            "Which 5 companies have the highest market value?",
            "How many companies are in each sector?",
            "What is the total revenue of companies in the Energy sector?",
            "Which states have the most Fortune 1000 company headquarters?",
            "Which Fortune 1000 companies are led by female CEOs?",
            "How many employees does Walmart have?"
        ]
        
        cols = st.columns(3)
        for i, example in enumerate(examples):
            col_idx = i % 3
            if cols[col_idx].button(example, key=f"example_{i}"):
                with st.spinner("Generating answer..."):
                    # Get answer from the agent
                    answer = agent.query(example)
                    st.markdown("### Answer")
                    st.write(answer)
    
    with tab2:
        st.markdown("""
        Connect to your Jira instance and ask questions or perform actions using natural language.
        This assistant uses LangChain with Gemini to interact with your Jira projects.
        """)
        
        # Jira settings - no longer in an expander to avoid nesting issues
        st.subheader("Jira Settings")
        jira_settings()
        
        st.markdown("---")  # Add a horizontal line for visual separation
        
        # Initialize Jira agent
        jira_agent = init_jira_agent()
        
        if jira_agent and jira_agent.is_initialized():
            # Input for Jira question
            jira_question = st.text_area("Ask a question or give a command for Jira:", 
                                     "List my top 5 highest priority issues")
            
            if st.button("Send to Jira"):
                if jira_question:
                    with st.spinner("Communicating with Jira..."):
                        # Get answer from the agent
                        answer = jira_agent.query(jira_question)
                        st.markdown("### Response")
                        st.write(answer)
                else:
                    st.warning("Please enter a question or command.")
            
            # Example Jira questions
            st.markdown("### Example Jira Commands")
            jira_examples = [
                "List all projects",
                "Find issues assigned to me",
                "Create a new bug ticket in project XYZ about login failures",
                "Search for issues with 'performance' in the summary",
                "What are my open issues with high priority?",
                "Show recent activity on project ABC"
            ]
            
            cols = st.columns(2)
            for i, example in enumerate(jira_examples):
                col_idx = i % 2
                if cols[col_idx].button(example, key=f"jira_example_{i}"):
                    with st.spinner("Communicating with Jira..."):
                        # Get answer from the agent
                        answer = jira_agent.query(example)
                        st.markdown("### Response")
                        st.write(answer)
        else:
            st.info("Please configure your Jira credentials in the settings above to enable Jira integration.")

if __name__ == "__main__":
    main()
