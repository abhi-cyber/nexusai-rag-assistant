import os
import logging
from typing import Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class WhatsAppAgent:
    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        """
        Initialize the WhatsApp Agent with Twilio credentials
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: WhatsApp sender number (with whatsapp: prefix)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        
        # Ensure the number has the whatsapp: prefix
        if not self.from_number.startswith('whatsapp:'):
            self.from_number = f'whatsapp:{self.from_number}'
        
        try:
            self.client = Client(account_sid, auth_token)
            self.initialized = True
        except Exception as e:
            logger.error(f"Error initializing Twilio client: {str(e)}")
            self.initialized = False
            self.error_message = str(e)
    
    def is_initialized(self) -> bool:
        """Check if the WhatsApp agent was properly initialized"""
        return self.initialized
    
    def verify_connection(self) -> Dict[str, Any]:
        """Verify the connection to Twilio and return basic information"""
        if not self.initialized:
            return {"status": "error", "message": self.error_message}
        
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            return {
                "status": "success", 
                "message": f"Successfully connected to Twilio. Account: {account.friendly_name}"
            }
        except TwilioRestException as e:
            return {"status": "error", "message": f"Twilio connection error: {str(e)}"}
    
    def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message
        
        Args:
            to_number: Recipient WhatsApp number
            message: Message content
            
        Returns:
            Dictionary with message status and info
        """
        if not self.initialized:
            return {"status": "error", "message": self.error_message}
        
        try:
            # Ensure recipient number has whatsapp: prefix
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            # Send message via Twilio
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            return {
                "status": "success",
                "message_sid": message.sid,
                "details": f"Message sent to {to_number}"
            }
            
        except TwilioRestException as e:
            return {"status": "error", "message": f"Failed to send message: {str(e)}"}
    
    def process_incoming_message(self, from_number: str, message_body: str, 
                                sql_agent=None, jira_agent=None) -> str:
        """
        Process an incoming WhatsApp message using the available agents
        
        Args:
            from_number: Sender's WhatsApp number
            message_body: Message content
            sql_agent: SQL query agent instance (optional)
            jira_agent: Jira query agent instance (optional)
            
        Returns:
            Response message
        """
        try:
            if from_number.startswith('whatsapp:'):
                from_number = from_number[9:]
            
            if message_body.lower().startswith(("jira", "ticket", "issue")) and jira_agent and jira_agent.is_initialized():
                response = jira_agent.query(message_body)
                
                if len(response) > 1500:
                    response = response[:1500] + "... (message truncated due to length)"
                
                return response
            
            elif sql_agent:
                result = sql_agent.query(message_body)
                
                if result and "answer" in result:
                    response = result["answer"]
                    
                    if len(response) > 1500:
                        response = response[:1500] + "... (message truncated due to length)"
                    
                    return response
            
            # Default response if no agents could process the message
            return ("I'm sorry, I couldn't process your query. Please try asking a question about your "
                   "data or specify 'Jira' at the beginning for Jira-related queries.")
            
        except Exception as e:
            return f"Sorry, an error occurred while processing your message: {str(e)}"
