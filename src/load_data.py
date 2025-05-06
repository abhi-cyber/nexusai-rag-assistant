import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import glob

def load_csv_to_sqlite(csv_path, db_path, table_name=None):
    """
    Load a single CSV file into SQLite database
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    if not table_name:
        table_name = os.path.splitext(os.path.basename(csv_path))[0]
        table_name = ''.join(c.lower() if c.isalnum() else '_' for c in table_name)
        while '__' in table_name:
            table_name = table_name.replace('__', '_')
        table_name = table_name.strip('_')
    
    print(f"Loading data from {csv_path} into table {table_name}...")
    
    # Read with error handling for potential CSV issues
    try:
        df = pd.read_csv(csv_path)
        print(f"Data loaded successfully. Found {len(df)} rows.")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        try:
            df = pd.read_csv(csv_path, encoding='latin1')
            print(f"Data loaded with latin1 encoding. Found {len(df)} rows.")
        except Exception as e:
            print(f"Failed to load CSV with alternative encoding: {e}")
            raise
    
    # Clean column names - replace spaces and special characters
    df.columns = [col.strip().replace(' ', '_').replace('-', '_').replace('.', '').lower() for col in df.columns]
    
    print(f"Columns in {table_name}: {', '.join(df.columns)}")
    
    df = df.replace({'': None})
    
    conn_str = f'sqlite:///{db_path}'
    engine = create_engine(conn_str)
    
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Data saved to SQLite database: {db_path}, table: {table_name}")
    
    return df, table_name

def load_all_csvs_to_sqlite(data_folder, db_path):
    """
    Load all CSV files from a folder into SQLite database
    """
    if not os.path.exists(data_folder):
        raise FileNotFoundError(f"Data folder not found: {data_folder}")
    
    csv_files = glob.glob(os.path.join(data_folder, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {data_folder}")
        return []
    
    tables_info = []
    
    for csv_path in csv_files:
        try:
            _, table_name = load_csv_to_sqlite(csv_path, db_path)
            table_info = get_table_info(db_path, table_name)
            tables_info.append(table_info)
        except Exception as e:
            print(f"Error loading {csv_path}: {e}")
    
    return tables_info

def get_table_info(db_path, table_name):
    """
    Get table schema information to help the agent understand the data structure
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    column_info = []
    for col in columns:
        col_id, name, dtype, notnull, default_val, pk = col
        column_info.append(f"{name} ({dtype})")
    
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    sample_data = cursor.fetchall()
    
    conn.close()
    
    table_info = {
        "name": table_name,
        "columns": column_info,
        "sample_data": sample_data
    }
    
    return table_info

def get_all_tables_info(db_path):
    """
    Get schema information for all tables in the database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Tables in database: {', '.join(t[0] for t in tables)}")
    
    tables_info = []
    for (table_name,) in tables:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
        sample = cursor.fetchone()
        if sample:
            print(f"Sample from {table_name}: {sample}")
        
        tables_info.append(get_table_info(db_path, table_name))
    
    conn.close()
    
    return tables_info

def debug_database(db_path):
    """
    Debug function to print all tables and their schema
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("======= DATABASE DEBUG INFO =======")
    print(f"Database: {db_path}")
    print(f"Tables found: {len(tables)}")
    
    for (table_name,) in tables:
        print(f"\nTable: {table_name}")
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            col_id, name, dtype, notnull, default_val, pk = col
            print(f"  - {name} ({dtype})")
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        print(f"Row count: {row_count}")
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        sample_data = cursor.fetchall()
        if sample_data:
            print("Sample data (first 3 rows):")
            for row in sample_data:
                print(f"  {row}")
    
    print("=================================")
    conn.close()
