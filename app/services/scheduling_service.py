from datetime import datetime, timedelta
import pytz
from app.models.database import db
from app.models.models import Candidate, Recruiter, AvailabilitySlot, Interview, ConversationState
from app.services.google_calendar import GoogleCalendarService
from app.services.twilio_service import TwilioService
import json

class SchedulingService:
    """Service for handling scheduling logic"""
    
    def __init__(self):
        """Initialize the scheduling service"""
        self.calendar_service = GoogleCalendarService()
        self.twilio_service = TwilioService()
    
    def register_candidate(self, name, phone_number, email, position_applied):
        """Register a new candidate"""
        # Create new candidate
        print(f"Creating new candidate: {name} with phone {phone_number}")
        candidate = Candidate(
            name=name,
            phone_number=phone_number,
            email=email,
            position_applied=position_applied,
            status='pending'
        )
        
        db.session.add(candidate)
        db.session.commit()
        
        return candidate
    
    def register_recruiter(self, name, email, calendar_id=None):
        """Register a new recruiter"""
        # Check if recruiter already exists
        existing_recruiter = Recruiter.query.filter_by(email=email).first()
        if existing_recruiter:
            return existing_recruiter
        
        # Create new recruiter
        recruiter = Recruiter(
            name=name,
            email=email,
            calendar_id=calendar_id
        )
        
        db.session.add(recruiter)
        db.session.commit()
        
        return recruiter
    
    def add_candidate_availability(self, candidate_id, start_time, end_time):
        """Add availability slot for a candidate"""
        # Create new availability slot
        slot = AvailabilitySlot(
            start_time=start_time,
            end_time=end_time,
            is_available=True,
            candidate_id=candidate_id
        )
        
        db.session.add(slot)
        db.session.commit()
        
        return slot
    
    def add_recruiter_availability(self, recruiter_id, start_time, end_time):
        """Add availability slot for a recruiter"""
        # Create new availability slot
        slot = AvailabilitySlot(
            start_time=start_time,
            end_time=end_time,
            is_available=True,
            recruiter_id=recruiter_id
        )
        
        db.session.add(slot)
        db.session.commit()
        
        return slot
    
    def get_recruiter_availability_from_calendar(self, recruiter_id, start_date, end_date, duration_minutes=60):
        """Get recruiter availability from Google Calendar"""
        # Get recruiter
        recruiter = Recruiter.query.get(recruiter_id)
        if not recruiter:
            print(f"Recruiter with ID {recruiter_id} not found")
            return []
            
        if not recruiter.calendar_id:
            print(f"Recruiter {recruiter.name} has no calendar ID set")
            return []
        
        try:
            # Use the Google Calendar API to find real available slots
            print(f"Fetching real availability from Google Calendar for recruiter {recruiter.name}")
            print(f"Calendar ID: {recruiter.calendar_id}")
            print(f"Date range: {start_date} to {end_date}")
            
            # Get available slots from calendar
            available_slots = self.calendar_service.find_available_slots(
                recruiter.calendar_id,
                start_date,
                end_date,
                duration_minutes
            )
            
            if available_slots:
                print(f"Found {len(available_slots)} real available slots from Google Calendar")
                for slot in available_slots:
                    print(f"Available slot: {slot[0]} to {slot[1]}")
                return available_slots
            else:
                print("No available slots found from Google Calendar, using fallback mock slots")
        except Exception as e:
            print(f"Error fetching availability from Google Calendar: {e}")
            import traceback
            traceback.print_exc()
            print("Using fallback mock slots due to error")
        
        # Fallback to mock slots if Google Calendar fails or returns no slots
        mock_slots = []
        current_date = start_date
        
        # Generate slots for the next 7 days
        while current_date < end_date:
            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday or Sunday
                current_date = current_date + timedelta(days=1)
                continue
                
            # Morning slot (10-11 AM)
            slot_start = current_date.replace(hour=10, minute=0, second=0, microsecond=0)
            slot_end = slot_start + timedelta(hours=1)
            if slot_start >= start_date and slot_end <= end_date:
                mock_slots.append((slot_start, slot_end))
                print(f"Generated mock slot: {slot_start} to {slot_end}")
            
            # Afternoon slot (2-3 PM)
            slot_start = current_date.replace(hour=14, minute=0, second=0, microsecond=0)
            slot_end = slot_start + timedelta(hours=1)
            if slot_start >= start_date and slot_end <= end_date:
                mock_slots.append((slot_start, slot_end))
                print(f"Generated mock slot: {slot_start} to {slot_end}")
            
            # Move to the next day
            current_date = current_date + timedelta(days=1)
        
        print(f"Generated {len(mock_slots)} mock slots as fallback")
        return mock_slots
    
    def find_matching_slots(self, candidate_id, recruiter_id, start_date, end_date, duration_minutes=60):
        """Find matching availability slots between candidate and recruiter"""
        # Get candidate availability
        candidate_slots = AvailabilitySlot.query.filter_by(
            candidate_id=candidate_id,
            is_available=True
        ).filter(
            AvailabilitySlot.start_time >= start_date,
            AvailabilitySlot.end_time <= end_date
        ).all()
        
        # Get recruiter
        recruiter = Recruiter.query.get(recruiter_id)
        if not recruiter or not recruiter.calendar_id:
            return []
        
        # Get recruiter availability from calendar
        recruiter_slots = self.get_recruiter_availability_from_calendar(
            recruiter_id,
            start_date,
            end_date,
            duration_minutes
        )
        
        # Convert candidate slots to tuples for easier comparison
        candidate_slot_tuples = [(slot.start_time, slot.end_time) for slot in candidate_slots]
        
        # Find matching slots
        matching_slots = []
        for recruiter_start, recruiter_end in recruiter_slots:
            for candidate_start, candidate_end in candidate_slot_tuples:
                # Check if there's an overlap of at least duration_minutes
                overlap_start = max(recruiter_start, candidate_start)
                overlap_end = min(recruiter_end, candidate_end)
                
                if overlap_start < overlap_end:
                    overlap_duration = (overlap_end - overlap_start).total_seconds() / 60
                    
                    if overlap_duration >= duration_minutes:
                        # We found a matching slot
                        slot_end = overlap_start + timedelta(minutes=duration_minutes)
                        matching_slots.append((overlap_start, slot_end))
        
        return matching_slots
    
    def schedule_interview(self, candidate_id, recruiter_id, start_time, end_time):
        """Schedule an interview and create a calendar event"""
        # Get candidate and recruiter
        candidate = Candidate.query.get(candidate_id)
        recruiter = Recruiter.query.get(recruiter_id)
        
        if not candidate or not recruiter:
            print(f"Error: Candidate or recruiter not found. Candidate ID: {candidate_id}, Recruiter ID: {recruiter_id}")
            return None
        
        print(f"Scheduling interview:")
        print(f"Candidate: {candidate.name} ({candidate.email})")
        print(f"Recruiter: {recruiter.name} ({recruiter.email})")
        print(f"Time: {start_time} to {end_time}")
        
        # Create the interview in the database
        interview = Interview(
            start_time=start_time,
            end_time=end_time,
            status='scheduled',
            candidate_id=candidate_id,
            recruiter_id=recruiter_id
        )
        
        db.session.add(interview)
        db.session.commit()
        
        # Create the calendar event
        event_summary = f"Interview: {candidate.name} for {candidate.position_applied}"
        event_description = f"Interview with {candidate.name} for the {candidate.position_applied} position."
        
        # Set up attendees with proper roles
        attendees = [
            {'email': candidate.email, 'responseStatus': 'needsAction'},  # Candidate needs to respond
            {'email': recruiter.email, 'responseStatus': 'accepted'}  # Recruiter is automatically accepted
        ]
        
        try:
            # Create the calendar event in the recruiter's calendar
            event = self.calendar_service.create_event(
                recruiter.calendar_id or 'primary',  # Use primary calendar if no specific calendar ID
                event_summary,
                event_description,
                start_time,
                end_time,
                attendees
            )
            
            # Update the interview with the calendar event ID and URL
            if event and 'id' in event:
                interview.calendar_event_id = event.get('id')
                
                # Get the proper URL from the event response
                if 'htmlLink' in event:
                    interview.calendar_url = event.get('htmlLink')
                else:
                    # Create a generic URL if htmlLink is not available
                    interview.calendar_url = f"https://calendar.google.com/calendar/event?eid={event.get('id')}"
                
                db.session.commit()
                
                # Force a refresh of the event to ensure notifications are sent
                updated_event = self.calendar_service.get_event(
                    recruiter.calendar_id or 'primary',
                    event.get('id')
                )
                
                # Verify the event was created correctly
                verified = self.verify_calendar_event(
                    recruiter.calendar_id or 'primary',
                    event.get('id')
                )
                
                if not verified:
                    print("Warning: Calendar event verification failed, but proceeding with interview scheduling")
                
                print(f"Calendar event created successfully. Event ID: {event.get('id')}")
                print(f"Calendar URL: {interview.calendar_url}")
                print(f"Calendar invites sent to: {candidate.email} and {recruiter.email}")
                
                # Send confirmation messages
                self.send_interview_confirmation(candidate.phone_number, candidate.name, recruiter.name, start_time, end_time)
                
                return interview
            else:
                print("Error: No event ID returned from calendar service")
                return None
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            import traceback
            traceback.print_exc()
            # Even if calendar event creation fails, we still want to keep the interview record
            return interview
    
    def send_interview_confirmation(self, phone_number, candidate_name, recruiter_name, start_time, end_time):
        """Send interview confirmation via WhatsApp"""
        # Format the date and time
        date_str = start_time.strftime("%A, %B %d, %Y")
        start_time_str = start_time.strftime("%I:%M %p")
        end_time_str = end_time.strftime("%I:%M %p")
        
        # Create the message
        message = f"Hello {candidate_name},\n\n"
        message += f"Your interview has been scheduled with {recruiter_name} on {date_str} "
        message += f"from {start_time_str} to {end_time_str}.\n\n"
        message += "You will receive a calendar invitation shortly. "
        message += "Please confirm your attendance by replying 'confirm'.\n\n"
        message += "If you need to reschedule, please reply 'reschedule'."
        
        # Send the message
        self.twilio_service.send_whatsapp_message(phone_number, message)
    
    def get_or_create_conversation_state(self, phone_number):
        """Get or create a conversation state for a phone number"""
        # Check if conversation state exists - get the most recent one
        state = ConversationState.query.filter_by(phone_number=phone_number).order_by(ConversationState.created_at.desc()).first()
        
        if not state:
            # Create new conversation state
            state = ConversationState(
                phone_number=phone_number,
                current_state='initial',
                context={}
            )
            db.session.add(state)
            db.session.commit()
        
        return state
    
    def update_conversation_state(self, phone_number, new_state, context=None):
        """Update the conversation state"""
        try:
            # Import db at the beginning to avoid UnboundLocalError
            from app.models.database import db
            from app.models.models import ConversationState
            import json
            
            # Debug logging
            print(f"Updating state for {phone_number} from state to {new_state}")
            print(f"New context: {context}")
            
            # First try to get the existing state - get the most recent one
            state = ConversationState.query.filter_by(phone_number=phone_number).order_by(ConversationState.created_at.desc()).first()
            
            if state:
                # Update existing state
                print(f"Found existing state: {state.current_state}")
                print(f"Current context: {state.context}")
                
                # Update the state
                state.current_state = new_state
                
                # Update the context if provided
                if context is not None:
                    # Make sure context is a dictionary
                    if not isinstance(context, dict):
                        print(f"WARNING: Context is not a dictionary: {context}")
                        context = {}
                    
                    # If the existing context is not None, merge the new context with it
                    # This ensures we don't lose information from the previous state
                    if state.context is not None:
                        # Create a copy of the existing context
                        merged_context = state.context.copy() if isinstance(state.context, dict) else {}
                        
                        # Update with the new context
                        merged_context.update(context)
                        
                        # Use the merged context
                        context = merged_context
                        print(f"Merged context: {context}")
                    
                    # Convert to string and back to ensure deep copy
                    context_str = json.dumps(context)
                    state.context = json.loads(context_str)
                    
                    print(f"Updated context: {state.context}")
                
                # Commit the changes
                db.session.commit()
                
                # Force a refresh from the database to ensure we have the latest data
                db.session.refresh(state)
                
                # Verify the update by fetching again
                updated_state = ConversationState.query.filter_by(phone_number=phone_number).order_by(ConversationState.created_at.desc()).first()
                print(f"Verified state: {updated_state.current_state}")
                print(f"Verified context: {updated_state.context}")
                
                return state
            else:
                # Create new state
                print(f"Creating new state for {phone_number}")
                
                # Ensure context is a dictionary
                if context is None:
                    context = {}
                elif not isinstance(context, dict):
                    print(f"WARNING: Context is not a dictionary: {context}")
                    context = {}
                
                # Convert to string and back to ensure deep copy
                context_str = json.dumps(context)
                context_copy = json.loads(context_str)
                
                # Create new conversation state
                new_state_obj = ConversationState(
                    phone_number=phone_number,
                    current_state=new_state,
                    context=context_copy
                )
                
                db.session.add(new_state_obj)
                db.session.commit()
                
                # Force a refresh from the database to ensure we have the latest data
                db.session.refresh(new_state_obj)
                
                # Verify the creation
                created_state = ConversationState.query.filter_by(phone_number=phone_number).order_by(ConversationState.created_at.desc()).first()
                print(f"Created state: {created_state.current_state}")
                print(f"Created context: {created_state.context}")
                
                return new_state_obj
                
        except Exception as e:
            print(f"Error updating conversation state: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Try one more approach as a last resort
            try:
                from app.models.database import db
                from app.models.models import ConversationState
                
                # We won't delete existing states anymore, just create a new one
                # Create a completely new state
                if context is None:
                    context = {}
                
                new_state_obj = ConversationState(
                    phone_number=phone_number,
                    current_state=new_state,
                    context=context
                )
                
                db.session.add(new_state_obj)
                db.session.commit()
                
                print(f"Created new state after error: {new_state}, context: {context}")
                
                return new_state_obj
            except Exception as inner_e:
                print(f"Failed to recover from error: {str(inner_e)}")
                traceback.print_exc()
                return None
    
    def reset_conversation(self, phone_number):
        """Reset the conversation state for a phone number"""
        conversation = ConversationState.query.filter_by(phone_number=phone_number).first()
        if conversation:
            db.session.delete(conversation)
            db.session.commit()
            print(f"Conversation state for {phone_number} has been reset")
            return True
        else:
            print(f"No conversation state found for {phone_number}")
            return False
            
    def parse_availability(self, message_text):
        """Parse availability from a message text"""
        # This is a simple implementation and can be enhanced with NLP
        try:
            # Example format: "Monday 2pm-4pm, Tuesday 10am-12pm"
            availability = []
            
            # Debug logging
            print(f"Parsing availability from: '{message_text}'")
            
            # Handle single day-time entry without comma
            if ',' not in message_text:
                parts = [message_text]
            else:
                parts = message_text.split(',')
            
            for part in parts:
                part = part.strip()
                print(f"Processing part: '{part}'")
                
                # Split by space to get day and time range
                segments = part.split()
                if len(segments) < 2:
                    print(f"Invalid format, not enough segments: {segments}")
                    continue
                
                # The first segment is the day, the rest combined is the time range
                day = segments[0].strip().lower()
                time_range = ' '.join(segments[1:]).strip()
                
                print(f"Day: '{day}', Time range: '{time_range}'")
                
                # Split time range by hyphen
                if '-' not in time_range:
                    print(f"Invalid time range format, missing hyphen: {time_range}")
                    continue
                
                time_parts = time_range.split('-')
                if len(time_parts) != 2:
                    print(f"Invalid time range format: {time_range}")
                    continue
                
                start_time_str = time_parts[0].strip().lower()
                end_time_str = time_parts[1].strip().lower()
                
                print(f"Start time: '{start_time_str}', End time: '{end_time_str}'")
                
                # Convert to datetime objects
                now = datetime.now()
                weekday_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2,
                    'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6,
                    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
                }
                
                if day not in weekday_map:
                    print(f"Invalid day: {day}")
                    continue
                
                # Calculate the date for the next occurrence of this weekday
                days_ahead = weekday_map[day] - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                
                target_date = now + timedelta(days=days_ahead)
                print(f"Target date: {target_date.strftime('%Y-%m-%d')}")
                
                # Parse time strings
                try:
                    # Handle various time formats
                    start_hour, start_minute = self._parse_time(start_time_str)
                    end_hour, end_minute = self._parse_time(end_time_str)
                    
                    print(f"Parsed start: {start_hour}:{start_minute}, end: {end_hour}:{end_minute}")
                    
                    start_time = target_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    end_time = target_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                    
                    print(f"Final start time: {start_time}, end time: {end_time}")
                    
                    availability.append((start_time, end_time))
                except ValueError as e:
                    print(f"Error parsing time: {e}")
                    continue
            
            print(f"Final availability slots: {availability}")
            return availability
        except Exception as e:
            print(f"Error parsing availability: {e}")
            return []
    
    def _parse_time(self, time_str):
        """Parse a time string into hour and minute components"""
        time_str = time_str.lower().strip()
        
        # Handle am/pm format
        is_pm = 'pm' in time_str
        time_str = time_str.replace('am', '').replace('pm', '').strip()
        
        # Handle hour:minute format
        if ':' in time_str:
            hour_str, minute_str = time_str.split(':')
            hour = int(hour_str)
            minute = int(minute_str)
        else:
            # Handle hour only format
            hour = int(time_str)
            minute = 0
        
        # Adjust for PM
        if is_pm and hour < 12:
            hour += 12
        
        # Validate hour and minute
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError(f"Invalid time: {hour}:{minute}")
        
        return hour, minute
    
    def verify_calendar_event(self, calendar_id, event_id):
        """Verify that a calendar event exists and has proper notifications"""
        try:
            event = self.calendar_service.get_event(calendar_id, event_id)
            if not event:
                print(f"Error: Could not retrieve event {event_id}")
                return False
                
            # Check if attendees are set correctly
            if 'attendees' not in event:
                print("Warning: No attendees found in event")
                return False
                
            print(f"Event verification successful for event {event_id}")
            return True
        except Exception as e:
            print(f"Error verifying calendar event: {e}")
            return False 