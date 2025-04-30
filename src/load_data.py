import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine

def load_csv_to_sqlite(csv_path, db_path='fortune1000.db', table_name='fortune1000'):
    """
    Load CSV data into SQLite database
    """
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Read CSV file
    print(f"Loading data from {csv_path}...")
    
    # Read with error handling for potential CSV issues
    try:
        df = pd.read_csv(csv_path)
        print(f"Data loaded successfully. Found {len(df)} rows.")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        # Try with different encoding
        try:
            df = pd.read_csv(csv_path, encoding='latin1')
            print(f"Data loaded with latin1 encoding. Found {len(df)} rows.")
        except Exception as e:
            print(f"Failed to load CSV with alternative encoding: {e}")
            raise
    
    # Clean column names - replace spaces and special characters
    df.columns = [col.strip().replace(' ', '_').replace('-', '_').replace('.', '').lower() for col in df.columns]
    
    # Convert empty strings to None for cleaner SQL
    df = df.replace({'': None})
    
    # Create SQLite database and save data
    conn_str = f'sqlite:///{db_path}'
    engine = create_engine(conn_str)
    
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Data saved to SQLite database: {db_path}, table: {table_name}")
    
    # Return dataframe and engine for reference
    return df, engine

def get_table_info(db_path='fortune1000.db', table_name='fortune1000'):
    """
    Get table schema information to help the agent understand the data structure
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get column information
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    # Format column information
    column_info = []
    for col in columns:
        col_id, name, dtype, notnull, default_val, pk = col
        column_info.append(f"{name} ({dtype})")
    
    # Get a sample of data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    sample_data = cursor.fetchall()
    
    conn.close()
    
    table_info = {
        "name": table_name,
        "columns": column_info,
        "sample_data": sample_data
    }
    
    return table_info
