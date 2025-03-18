import os
from app import create_app
from app.services.google_calendar import GoogleCalendarService
from app.models.models import Recruiter, Candidate
from app.models.database import db
from datetime import datetime, timedelta

def test_calendar_service():
    # Initialize the app context
    app = create_app()
    with app.app_context():
        # Create test data in the database
        recruiter_email = "recruiter@example.com"
        recruiter = Recruiter.query.filter_by(email=recruiter_email).first()
        if not recruiter:
            recruiter = Recruiter(
                name="Test Recruiter",
                email=recruiter_email,
                calendar_id="primary"  # Use "primary" for the default calendar
            )
            db.session.add(recruiter)
            db.session.commit()
            print(f"Created recruiter: {recruiter.name} with ID {recruiter.id}")
        else:
            print(f"Using existing recruiter: {recruiter.name} with ID {recruiter.id}")
        
        # Initialize the Google Calendar service
        calendar_service = GoogleCalendarService()
        
        # Create a test event
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        attendees = [
            {'email': recruiter.email, 'responseStatus': 'accepted'},
            {'email': 'test.candidate@example.com', 'responseStatus': 'needsAction'}
        ]
        
        print("Creating test calendar event...")
        
        try:
            event = calendar_service.create_event(
                calendar_id="primary",
                summary="Test Interview Event",
                description="This is a test event to verify calendar notifications are working",
                start_time=start_time,
                end_time=end_time,
                attendees=attendees
            )
            
            print(f"Event created successfully!")
            print(f"Event ID: {event.get('id')}")
            print(f"HTML Link: {event.get('htmlLink')}")
            
            if 'attendees' in event:
                print("Attendees:")
                for attendee in event['attendees']:
                    print(f"- {attendee.get('email')}: {attendee.get('responseStatus')}")
            
            # Get the event details to verify
            retrieved_event = calendar_service.get_event("primary", event.get('id'))
            print("\nVerifying event...")
            
            if retrieved_event:
                print("Event was successfully retrieved")
                print(f"Summary: {retrieved_event.get('summary')}")
                print(f"Description: {retrieved_event.get('description')}")
                
                if 'hangoutLink' in retrieved_event:
                    print(f"Meet Link: {retrieved_event.get('hangoutLink')}")
                
                return True
            else:
                print("Error: Could not retrieve the created event")
                return False
            
        except Exception as e:
            print(f"Error testing calendar service: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    test_calendar_service() 