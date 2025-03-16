import os
from dotenv import load_dotenv
from app import create_app
from app.models.database import db
from app.models.models import Recruiter

# Load environment variables
load_dotenv()

def init_db():
    """Initialize the database with default data"""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if there are any recruiters
        if Recruiter.query.count() == 0:
            # Create a default recruiter
            default_recruiter = Recruiter(
                name='Default Recruiter',
                email='recruiter@example.com',
                calendar_id='primary'  # Use the primary calendar
            )
            
            db.session.add(default_recruiter)
            db.session.commit()
            
            print('Default recruiter created.')
        else:
            print('Recruiters already exist. Skipping default recruiter creation.')
        
        print('Database initialized successfully.')

if __name__ == '__main__':
    init_db() 