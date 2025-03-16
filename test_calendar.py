import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.services.google_calendar import GoogleCalendarService

# Load environment variables
load_dotenv()

def test_calendar():
    """Test Google Calendar integration"""
    # Initialize Google Calendar service
    calendar_service = GoogleCalendarService()
    
    try:
        # Authenticate with Google Calendar
        service = calendar_service.authenticate()
        print("Authentication successful!")
        
        # Get calendar ID
        calendar_id = input("Enter calendar ID (leave blank for primary calendar): ") or 'primary'
        
        # Get available slots for the next 7 days
        now = datetime.now()
        end_date = now + timedelta(days=7)
        
        print(f"\nFinding available slots from {now.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        
        available_slots = calendar_service.find_available_slots(
            calendar_id,
            now,
            end_date,
            duration_minutes=60,
            working_hours=(9, 17)
        )
        
        if available_slots:
            print(f"\nFound {len(available_slots)} available slots:")
            for i, (start, end) in enumerate(available_slots[:10], 1):  # Show first 10 slots
                print(f"{i}. {start.strftime('%A, %B %d, %Y')} from {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}")
            
            # Ask if user wants to create a test event
            create_event = input("\nDo you want to create a test event? (y/n): ").lower() == 'y'
            
            if create_event:
                # Use the first available slot
                start_time = available_slots[0][0]
                end_time = available_slots[0][1]
                
                # Create a test event
                event = calendar_service.create_event(
                    calendar_id,
                    "Test Event",
                    "This is a test event created by the AI-Powered Scheduling Bot.",
                    start_time,
                    end_time,
                    [{'email': input("Enter your email address: ")}]
                )
                
                print(f"\nEvent created successfully! Event ID: {event.get('id')}")
                print(f"Event link: {event.get('htmlLink')}")
        else:
            print("No available slots found in the specified time range.")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    test_calendar() 