import os
from typing import Dict, List, Any, Optional
from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentType, initialize_agent

class JiraQueryAgent:
    def __init__(self, api_key: str, jira_config: Dict[str, Any]) -> None:
        """
        Initialize the Jira Query Agent with Gemini
        
        Args:
            api_key: Google API key for Gemini
            jira_config: Configuration for Jira
        """
        # Set the API key
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Set JIRA environment variables
        os.environ["JIRA_API_TOKEN"] = jira_config.get("api_token", "")
        os.environ["JIRA_USERNAME"] = jira_config.get("username", "")
        
        # Set JIRA instance URL
        os.environ["JIRA_INSTANCE_URL"] = jira_config.get("instance_url", "")
        
        # Set JIRA cloud flag
        os.environ["JIRA_CLOUD"] = str(jira_config.get("is_cloud", True))
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.2,
            convert_system_message_to_human=True
        )
        
        # Initialize Jira Wrapper
        try:
            self.jira = JiraAPIWrapper()
            self.toolkit = JiraToolkit.from_jira_api_wrapper(self.jira)
            
            # Initialize agent
            self.agent = initialize_agent(
                self.toolkit.get_tools(),
                self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,
                handle_parsing_errors=True
            )
            self.initialized = True
        except Exception as e:
            print(f"Error initializing Jira agent: {str(e)}")
            self.initialized = False
            self.error_message = str(e)
    
    def get_available_tools(self) -> List[str]:
        """Get a list of available Jira tools"""
        if not self.initialized:
            return []
        return [(tool.name, tool.description) for tool in self.toolkit.get_tools()]
    
    def query(self, question: str) -> str:
        """
        Process a natural language question about Jira
        
        Args:
            question: Natural language question about Jira
            
        Returns:
            Answer from the agent
        """
        if not self.initialized:
            return f"Jira agent not properly initialized: {self.error_message}"
        
        try:
            # Format the question to be specific to Jira
            enhanced_question = (
                f"Using the Jira tools available to you, please help with: {question}\n\n"
                "Provide a clear, direct response with the information requested."
            )
            
            # Run the agent
            response = self.agent.run(enhanced_question)
            return response
        except Exception as e:
            return f"Error processing your Jira question: {str(e)}"
    
    def is_initialized(self) -> bool:
        """Check if the Jira agent was properly initialized"""
        return self.initialized
    
    def verify_connection(self) -> Dict[str, Any]:
        """Verify the connection to Jira and return basic information"""
        if not self.initialized:
            return {"status": "error", "message": self.error_message}
        
        try:
            # Get projects safely
            projects = self.jira.jira.projects()
            
            # Extract project names, handling potential differences in structure
            project_names = []
            for project in projects[:5]:
                # Handle if project is a dictionary
                if isinstance(project, dict) and "name" in project:
                    project_names.append(project["name"])
                # Handle if project is an object with name attribute
                elif hasattr(project, "name"):
                    project_names.append(project.name)
                # Handle if project is an object with key attribute
                elif hasattr(project, "key"):
                    project_names.append(project.key)
                # If we can't extract a name, use a placeholder
                else:
                    project_names.append("Project " + str(projects.index(project) + 1))
            
            return {
                "status": "success", 
                "message": f"Successfully connected to Jira. Found {len(projects)} projects.",
                "projects": project_names
            }
        except Exception as e:
            return {"status": "error", "message": f"Connection error: {str(e)}"}
