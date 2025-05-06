import os
import pandas as pd
import sqlite3
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

class SQLQueryAgent:
    def __init__(self, api_key, db_path, tables_info):
        """
        Initialize the SQL Query Agent with multiple tables support
        
        Args:
            api_key: Google API key for Gemini
            db_path: Path to SQLite database
            tables_info: List of dictionaries containing table information
        """
        self.db_path = db_path
        self.tables_info = tables_info
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.2
        )
        
        self.create_prompt_templates()
    
    def create_prompt_templates(self):
        """Create the prompt templates for the LLM"""
        
        tables_description = ""
        for table in self.tables_info:
            tables_description += f"Table: {table['name']}\n"
            tables_description += f"Columns: {', '.join(table['columns'])}\n\n"
            
            if table['sample_data']:
                tables_description += "Sample data (first few rows):\n"
                sample_rows = []
                for row in table['sample_data'][:3]:  # Limit to 3 rows for brevity
                    sample_rows.append(str(row))
                tables_description += "\n".join(sample_rows)
                tables_description += "\n\n"
        
        # SQL generation prompt 
        sql_prompt_template = """
        You are a helpful SQL assistant that generates SQL queries based on natural language questions.

        Available tables in the database:
        {tables_description}

        Based on the above schema, write a SQL query to answer the following question:
        {question}

        Important guidelines:
        1. Determine which table(s) would be appropriate to query based on the question
        2. Use case-insensitive comparisons (LIKE with UPPER/LOWER or COLLATE NOCASE) for string searches
        3. Consider adding wildcards (%term%) when searching for company names or text fields
        4. Return ONLY the SQL query without any explanations - just the raw SQL query

        Example:
        For searching a company name like "Walmart", use:
        SELECT * FROM fortune1000_2024 WHERE UPPER(company) LIKE UPPER('%Walmart%')
        """
        
        self.sql_prompt = ChatPromptTemplate.from_template(sql_prompt_template)
        
        # Answer generation prompt
        answer_prompt_template = """
        You are a helpful data analysis assistant.

        The user asked: {question}

        The following SQL query was used to retrieve data from the database:
        {sql_query}

        The query returned the following results:
        {query_results}

        Please provide a clear, concise, and accurate answer to the user's question based on these results.
        Include specific numbers and facts from the data.
        If the query didn't return any results, suggest one of the following possibilities:
        1. There might be a spelling variation or case sensitivity issue
        2. The data might be in a different table than expected
        3. The information might not be present in the dataset
        
        Keep your answer focused on the data from the query results.
        """
        
        self.answer_prompt = ChatPromptTemplate.from_template(answer_prompt_template)
    
    def generate_sql(self, question):
        """Generate SQL query for the question"""
        sql_chain = LLMChain(llm=self.llm, prompt=self.sql_prompt)
        tables_description = ""
        for table in self.tables_info:
            tables_description += f"Table: {table['name']}\n"
            tables_description += f"Columns: {', '.join(table['columns'])}\n\n"
        
        result = sql_chain.run(tables_description=tables_description, question=question)
        return self.clean_sql_response(result)
    
    def clean_sql_response(self, sql_response):
        """Clean the SQL response to extract just the SQL query"""
        sql_response = re.sub(r'```sql|```', '', sql_response)
        sql_response = sql_response.strip()
        return sql_response
    
    def execute_sql(self, sql_query):
        """Execute SQL query and return results as DataFrame"""
        try:
            print(f"Executing SQL: {sql_query}")
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql_query, conn)
            print(f"Query returned {len(df)} rows")
            conn.close()
            return df
        except Exception as e:
            print(f"Error executing SQL: {e}")
            
            if "no such table" in str(e).lower():
                # List available tables
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [t[0] for t in cursor.fetchall()]
                conn.close()
                print(f"Available tables: {', '.join(tables)}")
            
            return pd.DataFrame()
    
    def generate_answer(self, question, sql_query, query_results):
        """Generate a natural language answer"""
        answer_chain = LLMChain(llm=self.llm, prompt=self.answer_prompt)
        
        if query_results.empty:
            results_str = "No results found."
        else:
            results_str = query_results.to_string()
        
        result = answer_chain.run(
            question=question,
            sql_query=sql_query,
            query_results=results_str
        )
        return result.strip()
    
    def query(self, question):
        """Process a natural language query and return results"""
        try:
            sql_query = self.generate_sql(question)
            
            data = self.execute_sql(sql_query)
            
            answer = self.generate_answer(question, sql_query, data)
            
            return {
                "answer": answer,
                "sql_query": sql_query,
                "data": data
            }
        except Exception as e:
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sql_query": "",
                "data": None
            }
