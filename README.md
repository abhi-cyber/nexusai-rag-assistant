# Fortune 1000 RAG SQL Assistant

This project demonstrates a Retrieval-Augmented Generation (RAG) system using LangChain's SQL Agent and Google's Gemini Flash 2.0 LLM to answer questions about Fortune 1000 companies data.

## Features

- Converts CSV data to a queryable SQLite database
- Uses LangChain with Google's Gemini Flash 2.0 for natural language to SQL translation
- Provides a friendly Streamlit UI for asking questions
- Answers questions by generating SQL queries and retrieving relevant information

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Get a Google API key for Gemini from https://ai.google.dev/
4. Add your API key to the `.env` file or enter it in the app when prompted
5. Run the application:
   ```
   streamlit run app.py
   ```

## How It Works

1. The application loads the Fortune 1000 CSV data into an SQLite database
2. When you ask a question in natural language, the Gemini LLM translates it to an SQL query
3. The query is executed against the database to retrieve relevant information
4. The LLM formats the results into a natural language response

## Example Questions

- Which companies in the technology sector have the highest revenue?
- Who are the female CEOs of Fortune 1000 companies?
- What's the average market value of companies in the Financials sector?
- Which states have the most Fortune 1000 headquarters?
- How many companies are in each industry category?
