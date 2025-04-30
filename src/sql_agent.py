import os
from typing import Dict, List, Any
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import pandas as pd
import re

class SQLQueryAgent:
    def __init__(self, db_path: str, api_key: str, table_info: Dict = None):
        """
        Initialize the SQL Query Agent with Gemini Flash
        
        Args:
            db_path: Path to SQLite database
            api_key: Google API key for Gemini
            table_info: Optional information about the table structure
        """
        # Set the API key
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Connect to the database
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        self.db_path = db_path
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            temperature=0.1,
            convert_system_message_to_human=True
        )
        
        # Store table information for context
        self.table_info = table_info
        
        # Create the SQL agent
        self.agent = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=False
        )
    
    def _generate_system_prompt(self, query: str) -> str:
        """Generate a detailed system prompt to guide the LLM"""
        
        base_prompt = """You are a helpful SQL expert. You will be given a database schema and a user question.
Your task is to write SQL to query the database to answer the user's question accurately.

Database Schema:
- Table: {table_name}
- Columns: {columns}

Think step by step:
1. Understand the question and identify the relevant columns needed
2. Consider any filters or conditions required
3. Determine if aggregations, groupings, or joins are necessary
4. Write a clean SQL query to answer the question
5. After getting results, provide a clear, concise explanation in natural language

User question: {query}
"""
        
        if self.table_info:
            return base_prompt.format(
                table_name=self.table_info["name"],
                columns=", ".join(self.table_info["columns"]),
                query=query
            )
        else:
            return base_prompt.format(
                table_name="fortune1000",
                columns="unknown - will explore database schema",
                query=query
            )
    
    def direct_query(self, sql_query):
        """Execute SQL query directly and return results"""
        import sqlite3
        
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            
            # Execute the query
            df = pd.read_sql_query(sql_query, conn)
            
            # Close connection
            conn.close()
            
            return df
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def query(self, question: str) -> str:
        """
        Process a natural language question and return an answer based on the database
        
        Args:
            question: Natural language question about the data
            
        Returns:
            Answer from the agent
        """
        try:
            # Check for specific common questions that can be handled directly
            question_lower = question.lower()
            
            # Direct handling for common simple queries
            if "how many employees" in question_lower and "walmart" in question_lower:
                # Execute direct SQL query for this specific case
                df = self.direct_query("SELECT company, number_of_employees FROM fortune1000 WHERE company = 'Walmart'")
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return f"Walmart has {df['number_of_employees'].values[0]:,} employees."
            
            # Direct handling for rank questions
            rank_match = re.search(r'(which|what).*company.*rank\s+(\d+)', question_lower)
            if rank_match:
                rank = rank_match.group(2)
                df = self.direct_query(f"SELECT company FROM fortune1000 WHERE rank = {rank}")
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return f"{df['company'].values[0]}"
            
            # Add context about the table structure to help the agent
            context = ""
            if self.table_info:
                context = f"The query is about the {self.table_info['name']} table. "
                context += f"The table has these columns: {', '.join(self.table_info['columns'])}. "
            
            # Enhanced question with clear instructions to provide only the direct answer
            enhanced_question = (f"{context}{question}\n\n"
                              "Important instructions: \n"
                              "1. DO NOT show any SQL commands in your response\n"
                              "2. DO NOT explain your thought process or reasoning\n"
                              "3. DO NOT prefix your answer with phrases like 'The answer is' or 'Based on the data'\n"
                              "4. ONLY provide the specific answer to the question - be direct and concise\n"
                              "5. Include actual values/numbers in your answer\n")
            
            # Get response from the agent
            response = self.agent.invoke({"input": enhanced_question})
            
            # Extract just the final answer from the response
            raw_answer = response.get("output", "")
            
            # Clean the answer to remove any SQL or explanations
            clean_answer = self._clean_response(raw_answer, question)
            
            return clean_answer
        
        except Exception as e:
            return f"Error processing your question: {str(e)}"
    
    def _clean_response(self, response: str, question: str) -> str:
        """Clean the response to contain only the direct answer"""
        
        # Remove any SQL code blocks or inline SQL
        response = re.sub(r'```sql.*?```', '', response, flags=re.DOTALL)
        response = re.sub(r'SELECT.*?FROM.*?;', '', response, flags=re.DOTALL)
        
        # Remove phrases that indicate thinking or analysis
        thinking_phrases = [
            "Based on the question,", "Based on the data,", "After executing the query,",
            "The query I will execute", "To answer this question", "I'll query the",
            "Looking at the data", "According to the database", "The SQL query shows",
            "The results show", "The answer is", "I found that"
        ]
        
        for phrase in thinking_phrases:
            response = response.replace(phrase, "")
        
        # Handle specific question types with cleaner responses
        if "rank" in question.lower() and "company" in question.lower():
            # For rank questions, try to extract just the company name
            company_match = re.search(r'is\s+([A-Za-z0-9\s\.&]+)\.?$', response)
            if company_match:
                return company_match.group(1).strip()
        
        # Further clean the response
        response = response.strip()
        response = re.sub(r'^[,:]\s*', '', response)  # Remove leading punctuation
        response = re.sub(r'\s+', ' ', response)      # Normalize whitespace
        
        return response
