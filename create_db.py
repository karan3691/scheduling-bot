import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the PostgreSQL database"""
    # Get database URL from environment variables
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        sys.exit(1)
    
    # Parse the database URL
    try:
        # Extract the database name from the URL
        db_parts = database_url.split('/')
        db_name = db_parts[-1]
        
        # Create a connection string without the database name
        conn_string = '/'.join(db_parts[:-1]) + '/postgres'
        
        # Connect to the default postgres database
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if the database already exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create the database
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        return False

if __name__ == '__main__':
    create_database() 