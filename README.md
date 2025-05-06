# Multi-Dataset RAG SQL Assistant

This project demonstrates a Retrieval-Augmented Generation (RAG) system using LangChain's SQL Agent and Google's Gemini Flash 2.0 LLM to answer questions about any dataset loaded from CSV files.

## Features

- Automatically loads any CSV files from the data folder into a queryable SQLite database
- Uses LangChain with Google's Gemini Flash 2.0 for natural language to SQL translation
- Provides a friendly Streamlit UI for asking questions
- Answers questions by generating SQL queries and retrieving relevant information
- Intelligently determines which dataset to query based on the question

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Get a Google API key for Gemini from https://ai.google.dev/
4. Add your API key to the `.env` file or enter it in the app when prompted
5. Add your CSV files to the `data` folder
6. Run the application:
   ```
   streamlit run app.py
   ```

## How It Works

1. The application automatically loads all CSV files from the data folder into an SQLite database
2. When you ask a question in natural language, the Gemini LLM translates it to an SQL query
3. The system determines which table(s) in the database are most relevant to your question
4. The query is executed against the database to retrieve relevant information
5. The LLM formats the results into a natural language response

## Example Questions

The types of questions you can ask depend on the datasets you've loaded. Here are some examples:

- Which items have the highest sales value?
- What is the average age of customers in the database?
- Show me the trends in product categories over the last year
- Which regions have the highest customer satisfaction scores?
- How many records are in each dataset?
