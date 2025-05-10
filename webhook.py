import os
import sys
import logging
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.load_data import get_all_tables_info
from src.sql_agent import SQLQueryAgent
from src.jira_agent import JiraQueryAgent

# Constants
DB_PATH = "datasets.db"

load_dotenv()

app = Flask(__name__)

def init_sql_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("Error: No Google API key found in environment variables")
        return None
        
    tables_info = get_all_tables_info(DB_PATH)
    if not tables_info:
        logger.error("Error: No tables found in the database")
        return None
    
    return SQLQueryAgent(api_key, DB_PATH, tables_info)

def init_jira_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return None
        
    jira_config = {
        "username": os.getenv("JIRA_USERNAME"),
        "api_token": os.getenv("JIRA_API_TOKEN"),
        "instance_url": os.getenv("JIRA_INSTANCE_URL"),
        "is_cloud": os.getenv("JIRA_CLOUD", "True").lower() == "true"
    }
    
    if not jira_config["instance_url"] or not jira_config["api_token"] or not jira_config["username"]:
        return None
        
    return JiraQueryAgent(api_key, jira_config)

@app.route('/', methods=['GET'])
def home():
    return "WhatsApp Webhook is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '')
    from_number = request.values.get('From', '')
    
    logger.info(f"Received message from {from_number}")
    
    resp = MessagingResponse()
    
    try:
        sql_agent = init_sql_agent()
        jira_agent = init_jira_agent()
        
        incoming_msg_lower = incoming_msg.lower()
        is_jira_query = any(keyword in incoming_msg_lower for keyword in ["jira", "ticket", "issue", "project"])
        
        if is_jira_query and jira_agent and jira_agent.is_initialized():
            result = jira_agent.query(incoming_msg)
            if result:
                if len(result) > 1500:
                    result = result[:1500] + "... (message truncated due to length)"
                resp.message(result)
            else:
                resp.message("I'm sorry, I couldn't find an answer to your Jira question.")
        elif sql_agent:
            result = sql_agent.query(incoming_msg)
            
            if result and "answer" in result:
                answer = result["answer"]
                
                if len(answer) > 1500:
                    answer = answer[:1500] + "... (message truncated due to length)"
                    
                resp.message(answer)
            else:
                resp.message("I'm sorry, I couldn't find an answer to your question.")
        else:
            resp.message("Sorry, I couldn't initialize the appropriate agent to answer your question.")
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        resp.message(f"Sorry, an error occurred: {str(e)}")
    
    return str(resp)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
