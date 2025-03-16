import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def drop_database():
    """Drop the PostgreSQL database"""
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
        
        # Check if the database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if exists:
            # Terminate all connections to the database
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid()
            """)
            
            # Drop the database
            cursor.execute(f"DROP DATABASE {db_name}")
            print(f"Database '{db_name}' dropped successfully.")
        else:
            print(f"Database '{db_name}' does not exist.")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error dropping database: {str(e)}")
        return False

if __name__ == '__main__':
    # Ask for confirmation
    confirm = input(f"Are you sure you want to drop the database? This will delete all data. (y/n): ")
    
    if confirm.lower() == 'y':
        drop_database()
    else:
        print("Operation cancelled.") 