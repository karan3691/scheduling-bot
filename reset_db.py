import os
import sys
from dotenv import load_dotenv
from drop_db import drop_database
from create_db import create_database
from init_db import init_db

# Load environment variables
load_dotenv()

def reset_database():
    """Reset the PostgreSQL database"""
    print("Resetting database...")
    
    # Drop the database
    if not drop_database():
        print("Error dropping database. Aborting reset.")
        return False
    
    # Create the database
    if not create_database():
        print("Error creating database. Aborting reset.")
        return False
    
    # Initialize the database
    init_db()
    
    print("Database reset completed successfully.")
    return True

if __name__ == '__main__':
    # Ask for confirmation
    confirm = input(f"Are you sure you want to reset the database? This will delete all data. (y/n): ")
    
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Operation cancelled.") 