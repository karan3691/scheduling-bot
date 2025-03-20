from datetime import datetime, timedelta
import re
from app.services.scheduling_service import SchedulingService
from app.models.models import Candidate, Recruiter, ConversationState

# Define parse_availability function in this file instead of importing it
def parse_availability(availability_text):
    """Parse user's availability text into datetime slots"""
    # Simple implementation to parse availability text
    available_slots = []
    
    try:
        # Current date and next 7 days
        now = datetime.now()
        
        # Split by commas for different day-time ranges
        day_times = [dt.strip() for dt in availability_text.split(',')]
        
        for day_time in day_times:
            # Try to find a pattern like "Monday 2pm-4pm"
            match = re.search(r'(\w+)\s+(\d+(?::\d+)?(?:am|pm)?)-(\d+(?::\d+)?(?:am|pm)?)', day_time, re.IGNORECASE)
            
            if match:
                day_name, start_time_str, end_time_str = match.groups()
                
                # Find the next occurrence of the given day
                target_day = now
                day_name_lower = day_name.lower()
                
                # Map day names to weekday numbers (0 = Monday, 6 = Sunday)
                day_map = {
                    'monday': 0, 'mon': 0,
                    'tuesday': 1, 'tue': 1, 'tues': 1,
                    'wednesday': 2, 'wed': 2,
                    'thursday': 3, 'thu': 3, 'thurs': 3,
                    'friday': 4, 'fri': 4,
                    'saturday': 5, 'sat': 5,
                    'sunday': 6, 'sun': 6,
                    'today': now.weekday(),
                    'tomorrow': (now.weekday() + 1) % 7
                }
                
                if day_name_lower in day_map:
                    target_weekday = day_map[day_name_lower]
                    days_ahead = (target_weekday - now.weekday()) % 7
                    if days_ahead == 0 and now.hour >= 17:  # If today but after 5pm, go to next week
                        days_ahead = 7
                    
                    target_day = now + timedelta(days=days_ahead)
                else:
                    # Try to parse as a date (e.g., "July 15")
                    try:
                        # This is a simplified approach, might need refinement
                        from dateutil import parser
                        parsed_date = parser.parse(day_name)
                        if parsed_date:
                            target_day = parsed_date
                    except Exception:
                        # If can't parse, skip this entry
                        continue
                
                # Parse start and end times
                try:
                    # Helper to parse time
                    def parse_time(time_str):
                        # Add default am/pm if not specified
                        if not ('am' in time_str.lower() or 'pm' in time_str.lower()):
                            if int(re.search(r'(\d+)', time_str).group(1)) < 12:
                                time_str += 'am'
                            else:
                                time_str += 'pm'
                        
                        # Simple parsing for common formats
                        if 'am' in time_str.lower():
                            hour = int(re.search(r'(\d+)', time_str).group(1))
                            hour = hour if hour != 12 else 0  # Handle 12am as 0
                            minute = 0
                            if ':' in time_str:
                                minute = int(re.search(r':(\d+)', time_str).group(1))
                            return hour, minute
                        else:  # pm
                            hour = int(re.search(r'(\d+)', time_str).group(1))
                            hour = hour if hour == 12 else hour + 12  # Handle 12pm and convert to 24h
                            minute = 0
                            if ':' in time_str:
                                minute = int(re.search(r':(\d+)', time_str).group(1))
                            return hour, minute
                    
                    start_hour, start_minute = parse_time(start_time_str)
                    end_hour, end_minute = parse_time(end_time_str)
                    
                    # Create datetime objects
                    start_datetime = target_day.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    end_datetime = target_day.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                    
                    # Handle case where end time wraps to next day
                    if end_datetime <= start_datetime:
                        end_datetime += timedelta(days=1)
                    
                    # Only add future slots (not past times)
                    if end_datetime > now:
                        available_slots.append((start_datetime, end_datetime))
                except Exception as e:
                    print(f"Error parsing time: {e}")
                    # Skip this entry if there's an error
                    continue
        
        # If no slots parsed correctly, try to create some based on the raw text
        if not available_slots:
            # Look for common patterns like "afternoons" or "mornings"
            text_lower = availability_text.lower()
            
            # Starting tomorrow, create slots for the next 3 days
            for i in range(1, 4):
                slot_day = now + timedelta(days=i)
                # Skip weekends
                if slot_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    continue
                    
                if "morning" in text_lower:
                    available_slots.append((
                        slot_day.replace(hour=9, minute=0, second=0, microsecond=0),
                        slot_day.replace(hour=12, minute=0, second=0, microsecond=0)
                    ))
                    
                if "afternoon" in text_lower:
                    available_slots.append((
                        slot_day.replace(hour=13, minute=0, second=0, microsecond=0),
                        slot_day.replace(hour=17, minute=0, second=0, microsecond=0)
                    ))
                    
                if "evening" in text_lower:
                    available_slots.append((
                        slot_day.replace(hour=17, minute=0, second=0, microsecond=0),
                        slot_day.replace(hour=19, minute=0, second=0, microsecond=0)
                    ))
                    
                # If they mention specific days
                for day, day_num in day_map.items():
                    if day in text_lower and day != "today" and day != "tomorrow":
                        # Find the next occurrence of this day
                        days_ahead = (day_num - now.weekday()) % 7
                        if days_ahead == 0:
                            days_ahead = 7  # Go to next week if today
                        
                        target_day = now + timedelta(days=days_ahead)
                        # Add a general afternoon slot
                        available_slots.append((
                            target_day.replace(hour=14, minute=0, second=0, microsecond=0),
                            target_day.replace(hour=16, minute=0, second=0, microsecond=0)
                        ))
        
        return available_slots
    except Exception as e:
        print(f"Error in parse_availability: {e}")
        import traceback
        traceback.print_exc()
        return []

class ConversationHandler:
    """Handler for WhatsApp conversations with candidates"""
    
    def __init__(self):
        """Initialize the conversation handler"""
        self.scheduling_service = SchedulingService()
    
    def handle_message(self, from_number, message_body):
        """Handle incoming WhatsApp messages"""
        try:
            # Make sure we have valid input
            if not from_number or not message_body:
                print("Missing from_number or message_body")
                return "Hello! I'm your interview scheduling assistant. Please send 'hi' or 'hello' to start."
                
            # Clean the phone number (remove 'whatsapp:' prefix if present)
            phone_number = from_number.replace('whatsapp:', '')
            
            # Ensure phone number starts with + if it's a digit and doesn't have it
            if phone_number and phone_number[0].isdigit() and not phone_number.startswith('+'):
                phone_number = '+' + phone_number
                
            print(f"Cleaned phone number: {phone_number}")
            
            # Check for greeting keywords - prioritize this check
            greeting_keywords = ['hi', 'hello', 'hey', 'hola', 'start', 'begin']
            if message_body.lower().strip() in greeting_keywords:
                print(f"Greeting detected, resetting conversation for {phone_number}")
                # Reset any existing conversation
                self.scheduling_service.reset_conversation(phone_number)
                # Create a new conversation state at awaiting_name
                self.scheduling_service.update_conversation_state(phone_number, 'awaiting_name', {})
                return "Welcome to our interview scheduling assistant! 👋\n\nI'll help you schedule an interview with our recruitment team. To get started, please tell me your full name."
            
            # Check for reset command
            if message_body.lower().strip() in ['reset', 'restart', 'start over']:
                print(f"Resetting conversation for {phone_number}")
                self.scheduling_service.reset_conversation(phone_number)
                return "Conversation has been reset. Let's start over! Please tell me your full name."
            
            # Get or create conversation state
            state = self.scheduling_service.get_or_create_conversation_state(phone_number)
            
            # Debug logging
            print(f"Handling message from {phone_number}")
            print(f"Current state: {state.current_state}")
            print(f"Message: '{message_body}'")
            
            # Check for calendar invitation query
            if any(keyword in message_body.lower() for keyword in ['calendar', 'invitation', 'invite', 'received', 'check']):
                # Check if the user has any scheduled interviews
                from app.models.models import Candidate, Interview
                candidate = Candidate.query.filter_by(phone_number=phone_number).first()
                
                if not candidate:
                    return "I don't have any record of your registration. Please start over by sending 'hi' or 'hello'."
                
                interviews = Interview.query.filter_by(candidate_id=candidate.id).all()
                
                if not interviews:
                    return "You don't have any scheduled interviews yet. Would you like to schedule one? Send 'hi' or 'hello' to start."
                
                # Format the interview details
                response = "Here are your scheduled interviews:\n\n"
                
                for i, interview in enumerate(interviews, 1):
                    date_str = interview.start_time.strftime("%A, %B %d, %Y")
                    start_time_str = interview.start_time.strftime("%I:%M %p")
                    end_time_str = interview.end_time.strftime("%I:%M %p")
                    
                    response += f"{i}. {date_str} from {start_time_str} to {end_time_str} - Status: {interview.status}\n"
                
                response += "\nThe calendar invitation should have been sent to your email. Please check your inbox, including spam/junk folders."
                response += "\nIf you haven't received it, please contact our recruitment team or reply 'resend' to request another invitation."
                
                return response
            
            # Check if this is a continue command
            if message_body.lower() == 'continue':
                # Provide appropriate response based on current state
                if state.current_state == 'awaiting_name':
                    return "Please tell me your full name."
                elif state.current_state == 'awaiting_email':
                    return "Please provide your email address so we can send you the calendar invitation."
                elif state.current_state == 'awaiting_position':
                    return "For which position are you interviewing?"
                elif state.current_state == 'awaiting_availability':
                    return ("Please share your availability for the interview.\n\n"
                           "Please format your availability as follows:\n"
                           "day time-time, day time-time\n\n"
                           "For example: Monday 2pm-4pm, Tuesday 10am-12pm")
                elif state.current_state == 'awaiting_slot_selection':
                    # Generate slots again
                    return self.handle_slot_selection_state(phone_number, "show_slots", state)
                elif state.current_state == 'awaiting_confirmation':
                    return "Please confirm by replying 'yes' or 'no'."
                else:
                    return "Let's continue. Please send 'hi' or 'hello' to start."
            
            # Handle message based on current state
            if state.current_state == 'initial':
                return self.handle_initial_state(phone_number, message_body)
            elif state.current_state == 'awaiting_name':
                return self.handle_name_state(phone_number, message_body, state)
            elif state.current_state == 'awaiting_email':
                return self.handle_email_state(phone_number, message_body, state)
            elif state.current_state == 'awaiting_position':
                return self.handle_position_state(phone_number, message_body, state)
            elif state.current_state == 'awaiting_availability':
                return self.handle_availability_state(phone_number, message_body, state)
            elif state.current_state == 'awaiting_slot_selection':
                return self.handle_slot_selection_state(phone_number, message_body, state)
            elif state.current_state == 'awaiting_confirmation':
                return self.handle_confirmation_state(phone_number, message_body, state)
            else:
                # Unknown state, reset to initial
                self.scheduling_service.update_conversation_state(phone_number, 'initial', {})
                return "I'm sorry, there was an error with the conversation state. Please start over by sending 'hi' or 'hello'."
                
        except Exception as e:
            print(f"Error in handle_message: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, there was an error processing your message. Please try again by sending 'hi' or 'hello'."
    
    def handle_initial_state(self, phone_number, message_body):
        """Handle initial state"""
        # Check if message is a greeting
        if message_body.lower() in ['hi', 'hello', 'hey', 'start']:
            try:
                # Always reset the state when user sends a greeting in initial state
                # This ensures they can start a new conversation
                self.scheduling_service.update_conversation_state(phone_number, 'awaiting_name', {})
                
                return ("Welcome to our interview scheduling assistant! 👋\n\n"
                       "I'll help you schedule an interview with our recruitment team. "
                       "To get started, please tell me your full name.")
            except Exception as e:
                print(f"Error in handle_initial_state: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Try to reset the conversation state
                try:
                    from app.models.database import db
                    from app.models.models import ConversationState
                    
                    # Create new state without deleting existing ones
                    new_state = ConversationState(
                        phone_number=phone_number,
                        current_state='awaiting_name',
                        context={}
                    )
                    db.session.add(new_state)
                    db.session.commit()
                    
                    return ("Welcome to our interview scheduling assistant! 👋\n\n"
                           "I'll help you schedule an interview with our recruitment team. "
                           "To get started, please tell me your full name.")
                except Exception as inner_e:
                    print(f"Failed to reset conversation state: {str(inner_e)}")
                    traceback.print_exc()
                    return "I'm sorry, there was an error with the system. Please try again later."
        else:
            return ("Hello! I'm your interview scheduling assistant. 👋\n\n"
                   "To start scheduling your interview, please send 'hi' or 'hello'.")
    
    def handle_name_state(self, phone_number, message_body, state):
        """Handle awaiting name state"""
        # Validate name (simple validation, can be enhanced)
        name = message_body.strip()
        
        # Accept any name, even short ones like "Hi"
        try:
            # Debug logging
            print(f"Phone number: {phone_number}")
            print(f"Current state: {state.current_state}")
            print(f"Name: {name}")
            
            # Create context with name
            context = {'name': name}
            
            # Debug logging
            print(f"Context with name: {context}")
            
            # Update state with name and move to email
            self.scheduling_service.update_conversation_state(
                phone_number, 
                'awaiting_email',
                context
            )
            
            return f"Thanks, {name}! Please provide your email address so we can send you the calendar invitation."
        except Exception as e:
            # Log the error and return a friendly message
            print(f"Error in handle_name_state: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, there was an error processing your request. Please try again or contact support."
    
    def handle_email_state(self, phone_number, message_body, state):
        """Handle awaiting email state"""
        # Validate email
        email = message_body.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return "Please provide a valid email address (e.g., name@example.com)."
        
        try:
            # Get the current context
            context = state.context if state.context is not None else {}
            
            # Debug logging
            print(f"Phone number: {phone_number}")
            print(f"Current state: {state.current_state}")
            print(f"Context before adding email: {context}")
            
            # Add email to context
            context['email'] = email
            
            # Debug logging
            print(f"Context after adding email: {context}")
            
            # We no longer update existing candidates
            # Just log that we found an existing candidate for debugging
            from app.models.models import Candidate
            existing_candidate = Candidate.query.filter_by(phone_number=phone_number).order_by(Candidate.created_at.desc()).first()
            if existing_candidate:
                print(f"Found existing candidate: {existing_candidate.id} - {existing_candidate.name} - {existing_candidate.email}")
                print(f"Will create a new candidate with email: {email}")
            
            # Force update the context directly in the database first to ensure it persists
            from app.models.database import db
            from app.models.models import ConversationState
            
            state_record = ConversationState.query.filter_by(phone_number=phone_number).first()
            if state_record:
                import json
                context_copy = state_record.context.copy() if state_record.context else {}
                context_copy['email'] = email
                state_record.context = context_copy
                db.session.commit()
                print(f"Forced context update before state change: {state_record.context}")
            
            # Update conversation state
            self.scheduling_service.update_conversation_state(
                phone_number, 
                'awaiting_position',
                context
            )
            
            # Double-check that the email was saved in the context
            updated_state = self.scheduling_service.get_or_create_conversation_state(phone_number)
            print(f"Verifying email was saved: {updated_state.context}")
            
            if 'email' not in updated_state.context or updated_state.context.get('email') != email:
                print("WARNING: Email was not saved correctly in context, forcing update again")
                # Force update the context directly in the database again
                state_record = ConversationState.query.filter_by(phone_number=phone_number).first()
                if state_record:
                    context_copy = state_record.context.copy() if state_record.context else {}
                    context_copy['email'] = email
                    state_record.context = context_copy
                    db.session.commit()
                    print(f"Forced context update after state change: {state_record.context}")
            
            return "Great! For which position are you interviewing?"
        except Exception as e:
            # Log the error and return a friendly message
            print(f"Error in handle_email_state: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, there was an error processing your request. Please try again or contact support."
    
    def handle_position_state(self, phone_number, message_body, state):
        """Handle awaiting position state"""
        # Validate position (simple validation, can be enhanced)
        position = message_body.strip()
        if len(position) < 2:
            return "Please provide a valid position with at least 2 characters."
        
        try:
            # Get the current context
            context = state.context if state.context is not None else {}
            
            # Add position to context
            context['position'] = position
            
            # Debug logging
            print(f"Phone number: {phone_number}")
            print(f"Current state: {state.current_state}")
            print(f"Context before registration: {context}")
            
            # Check if candidate already exists
            from app.models.models import Candidate
            existing_candidate = Candidate.query.filter_by(phone_number=phone_number).first()
            
            # For debugging, let's check for missing fields and try to recover them
            if 'name' not in context:
                print("WARNING: Name missing from context, trying to recover from database")
                if existing_candidate:
                    context['name'] = existing_candidate.name
                    print(f"Recovered name from database: {context['name']}")
                else:
                    print("WARNING: No existing candidate found, using default name")
                    context['name'] = "Default User"
            
            # Force read the context from the database to ensure we have the most recent version
            from app.models.models import ConversationState
            from app.models.database import db
            db_state = ConversationState.query.filter_by(phone_number=phone_number).first()
            if db_state and db_state.context:
                # Update missing fields in our context from the database context
                for key, value in db_state.context.items():
                    if key not in context or not context[key]:
                        context[key] = value
                        print(f"Updated {key} from database context: {value}")
            
            # Check if email is in the context - this is the key part
            print(f"Checking for email in context: {context}")
            if 'email' not in context or not context['email']:
                print("WARNING: Email missing from context, trying to recover from database")
                
                # First, try to get the email from the existing candidate
                if existing_candidate and existing_candidate.email != "default@example.com":
                    # Use the existing email from the database
                    context['email'] = existing_candidate.email
                    print(f"Recovered email from database: {context['email']}")
                else:
                    # Check if we can find the candidate in the database by name
                    candidate_by_name = Candidate.query.filter_by(name=context['name']).first()
                    if candidate_by_name and candidate_by_name.email != "default@example.com":
                        context['email'] = candidate_by_name.email
                        print(f"Recovered email from database by name: {context['email']}")
                    else:
                        # If we still don't have an email, check if there's a previous conversation state
                        prev_state = ConversationState.query.filter_by(phone_number=phone_number).first()
                        if prev_state and prev_state.context and 'email' in prev_state.context:
                            context['email'] = prev_state.context['email']
                            print(f"Recovered email from previous conversation state: {context['email']}")
                        else:
                            # If we still don't have an email, prompt the user to provide one
                            # First, save the current context with the position
                            self.scheduling_service.update_conversation_state(
                                phone_number, 
                                'awaiting_email',
                                context
                            )
                            return "I need your email address to schedule the interview. Please provide your email address."
            else:
                print(f"Email found in context: {context['email']}")
            
            # At this point, we should have both name and email in the context
            print(f"Final context before registration: {context}")
            
            # Always create a new candidate, even if one already exists with the same phone number
            print(f"Registering new candidate: {context['name']}, {phone_number}, {context['email']}, {position}")
            candidate = self.scheduling_service.register_candidate(
                context['name'],
                phone_number,
                context['email'],
                position
            )
            
            # Create a new context with all necessary information
            new_context = {
                'candidate_id': candidate.id,
                'name': context['name'],
                'email': context['email'],
                'position': position
            }
            
            print(f"New context for availability state: {new_context}")
            
            # Update conversation state
            self.scheduling_service.update_conversation_state(
                phone_number, 
                'awaiting_availability',
                new_context
            )
            
            # Force update the context directly in the database to ensure it persists
            db_state = ConversationState.query.filter_by(phone_number=phone_number).first()
            if db_state:
                db_state.context = new_context
                db.session.commit()
                print(f"Forced context update after state change: {db_state.context}")
            
            # Double-check that the context was saved correctly
            updated_state = self.scheduling_service.get_or_create_conversation_state(phone_number)
            print(f"Verifying context was saved: {updated_state.context}")
            
            return ("Thanks for the information! Now, please share your availability for the interview.\n\n"
                   "Please format your availability as follows:\n"
                   "day time-time, day time-time\n\n"
                   "For example: Monday 2pm-4pm, Tuesday 10am-12pm\n\n"
                   "Please provide your availability for the next 7 days.")
        except Exception as e:
            # Log the error and return a friendly message
            print(f"Error in handle_position_state: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, there was an error processing your request. Please try again or contact support."
    
    def handle_availability_state(self, phone_number, message_body, state):
        """Handle awaiting availability state"""
        try:
            # Get context
            context = state.context if state.context is not None else {}
            
            # Simple validation - we're just checking if there's content
            if not message_body or len(message_body.strip()) < 5:
                return "I couldn't understand your availability. Please provide it in the format: day time-time, day time-time. For example: Monday 2pm-4pm, Tuesday 10am-12pm"
            
            # Store the raw availability message
            context['raw_availability'] = message_body
            
            # Parse the availability using our function
            available_slots = parse_availability(message_body)
            
            if not available_slots:
                return "I couldn't understand your availability format. Please try again with the format: day time-time (e.g., 'Monday 2pm-4pm, Tuesday 10am-12pm')"
            
            # Get the candidate
            candidate_id = context.get('candidate_id')
            if not candidate_id:
                return "I'm having trouble with your registration. Please start over by sending 'hi' or 'hello'."
            
            # Get the first available recruiter
            from app.models.models import Recruiter
            recruiter = Recruiter.query.first()
            if not recruiter:
                return "I'm sorry, there are no recruiters available at the moment. Please try again later."
            
            # Check recruiter's calendar for availability 
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
            
            # Get the recruiter's availability from Google Calendar
            real_available_slots = []
            try:
                # Get the recruiter's free slots from their calendar
                recruiter_slots = self.scheduling_service.get_recruiter_availability_from_calendar(
                    recruiter.id, 
                    start_date, 
                    end_date
                )
                
                # Filter slots based on candidate's availability
                for recruiter_slot_start, recruiter_slot_end in recruiter_slots:
                    for candidate_slot in available_slots:
                        candidate_slot_start, candidate_slot_end = candidate_slot
                        
                        # Check if slots overlap
                        if (candidate_slot_start <= recruiter_slot_end and 
                            candidate_slot_end >= recruiter_slot_start):
                            
                            # Find the overlap
                            overlap_start = max(candidate_slot_start, recruiter_slot_start)
                            overlap_end = min(candidate_slot_end, recruiter_slot_end)
                            
                            # Only use if the overlap is at least 30 minutes
                            if (overlap_end - overlap_start).total_seconds() >= 30 * 60:
                                real_available_slots.append((overlap_start, overlap_end))
                
                if not real_available_slots:
                    # If no matching slots, try with more flexible recruiter slots
                    for candidate_slot in available_slots:
                        candidate_day = candidate_slot[0].date()
                        # Create a 1-hour slot in the middle of the candidate's availability
                        candidate_slot_start, candidate_slot_end = candidate_slot
                        duration = (candidate_slot_end - candidate_slot_start).total_seconds() / 60
                        if duration >= 60:
                            midpoint = candidate_slot_start + (candidate_slot_end - candidate_slot_start) / 2
                            slot_start = midpoint - timedelta(minutes=30)
                            slot_end = midpoint + timedelta(minutes=30)
                            real_available_slots.append((slot_start, slot_end))
            except Exception as e:
                print(f"Error checking recruiter calendar: {str(e)}")
                import traceback
                traceback.print_exc()
                # Fall back to mock slots based on candidate availability
                for slot in available_slots:
                    # Use the first hour of each candidate slot
                    slot_start, slot_end = slot
                    adjusted_end = slot_start + timedelta(hours=1)
                    if adjusted_end <= slot_end:
                        real_available_slots.append((slot_start, adjusted_end))
                    else:
                        real_available_slots.append((slot_start, slot_end))
            
            # If still no slots, create mock slots
            if not real_available_slots:
                # Create mock slots (business hours for the next 3 days)
                start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
                if start_date.hour >= 17:
                    start_date = start_date + timedelta(days=1)
                
                mock_slots = []
                for i in range(3):
                    current_date = start_date + timedelta(days=i)
                    # Skip weekends
                    if current_date.weekday() >= 5:  # Saturday or Sunday
                        continue
                        
                    # Morning slot
                    mock_slots.append((
                        current_date.replace(hour=10, minute=0),
                        current_date.replace(hour=11, minute=0)
                    ))
                    
                    # Afternoon slot
                    mock_slots.append((
                        current_date.replace(hour=14, minute=0),
                        current_date.replace(hour=15, minute=0)
                    ))
                
                real_available_slots = mock_slots
            
            # Limit to 3 slots for simplicity
            if len(real_available_slots) > 3:
                real_available_slots = real_available_slots[:3]
            
            # Format the slots for display and save in context
            formatted_slots = []
            iso_slots = []
            
            for slot_start, slot_end in real_available_slots:
                formatted_slot = f"{slot_start.strftime('%A, %B %d')} from {slot_start.strftime('%I:%M %p')} to {slot_end.strftime('%I:%M %p')}"
                formatted_slots.append(formatted_slot)
                iso_slots.append([slot_start.isoformat(), slot_end.isoformat()])
            
            # Save the available slots in the context
            context['available_slots'] = iso_slots
            
            # Update conversation state
            self.scheduling_service.update_conversation_state(
                phone_number, 
                'awaiting_slot_selection',
                context
            )
            
            # Build the response
            response = "Great! Based on your availability and the recruiter's calendar, here are some possible interview slots:\n\n"
            
            for i, slot in enumerate(formatted_slots, 1):
                response += f"{i}. {slot}\n"
            
            response += "\nPlease reply with the number of your preferred slot (e.g., '1', '2', or '3')."
            
            return response
        except Exception as e:
            # Log the error and return a friendly message
            print(f"Error in handle_availability_state: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, there was an error processing your availability. Please try again or contact support."
    
    def handle_slot_selection_state(self, phone_number, message_body, state):
        """Handle awaiting slot selection state"""
        try:
            # Debug logging
            print(f"Phone number: {phone_number}")
            print(f"Current state: {state.current_state}")
            print(f"Message body: '{message_body}'")
            print(f"Context: {state.context}")
            
            # Always generate new slots regardless of context
            # This ensures we always have slots to show
            
            # Find candidate - get the most recent one with this phone number
            from app.models.models import Candidate
            candidate = Candidate.query.filter_by(phone_number=phone_number).order_by(Candidate.created_at.desc()).first()
            
            if not candidate:
                print("No candidate found for phone number")
                return "I'm sorry, there was an error with your registration. Please start over by sending 'hi' or 'hello'."
            
            # Find recruiter
            from app.models.models import Recruiter
            recruiter = Recruiter.query.first()
            
            if not recruiter:
                print("No recruiters found in database")
                return "I'm sorry, there are no recruiters available at the moment. Please try again later."
            
            # Generate mock slots
            now = datetime.now()
            mock_slots = []
            for i in range(3):  # Generate 3 mock slots
                slot_date = now + timedelta(days=i+1)
                # Make sure it's a weekday
                while slot_date.weekday() >= 5:  # Skip weekends
                    slot_date = slot_date + timedelta(days=1)
                
                # Create a slot at 2pm
                start_time = slot_date.replace(hour=14, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(hours=1)
                mock_slots.append((start_time, end_time))
                
                # Create another slot at 4pm
                start_time = slot_date.replace(hour=16, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(hours=1)
                mock_slots.append((start_time, end_time))
            
            # Check if this is a special command to show slots
            if message_body == "show_slots":
                # Show the slots
                slot_options = "Here are the available interview slots:\n\n"
                for i, (start, end) in enumerate(mock_slots[:5], 1):
                    date_str = start.strftime("%A, %B %d, %Y")
                    start_time_str = start.strftime("%I:%M %p")
                    end_time_str = end.strftime("%I:%M %p")
                    slot_options += f"{i}. {date_str} from {start_time_str} to {end_time_str}\n"
                
                slot_options += "\nPlease reply with the number of your preferred slot (e.g., '1', '2', etc.)."
                
                # Update context with the slots and candidate information
                context = {
                    'candidate_id': candidate.id,
                    'recruiter_id': recruiter.id,
                    'name': candidate.name,
                    'email': candidate.email,  # Use actual email from database
                    'position': candidate.position_applied
                }
                
                print(f"Using email from database: {candidate.email}")
                
                self.scheduling_service.update_conversation_state(
                    phone_number, 
                    'awaiting_slot_selection',
                    context
                )
                
                return slot_options
            
            # Try to parse the selection
            try:
                selection = int(message_body.strip())
                print(f"User selected option: {selection}")
                
                if selection < 1 or selection > len(mock_slots):
                    print(f"Invalid selection: {selection}, valid range is 1-{len(mock_slots)}")
                    
                    # Show the slots again
                    slot_options = "Please select a valid option. Here are the available slots:\n\n"
                    for i, (start, end) in enumerate(mock_slots[:5], 1):
                        date_str = start.strftime("%A, %B %d, %Y")
                        start_time_str = start.strftime("%I:%M %p")
                        end_time_str = end.strftime("%I:%M %p")
                        slot_options += f"{i}. {date_str} from {start_time_str} to {end_time_str}\n"
                    
                    slot_options += "\nPlease reply with the number of your preferred slot (e.g., '1', '2', etc.)."
                    return slot_options
                
                # Get the selected slot
                selected_slot = mock_slots[selection - 1]
                start_time = selected_slot[0]
                end_time = selected_slot[1]
                
                print(f"Selected slot: {start_time} - {end_time}")
                print(f"Using email from database: {candidate.email}")
                
                # Create a new context with all the necessary information
                context = {
                    'candidate_id': candidate.id,
                    'recruiter_id': recruiter.id,
                    'selected_slot': (start_time.isoformat(), end_time.isoformat()),
                    'name': candidate.name,
                    'email': candidate.email,  # Use actual email from database
                    'position': candidate.position_applied
                }
                
                # Update the state
                self.scheduling_service.update_conversation_state(
                    phone_number, 
                    'awaiting_confirmation',
                    context
                )
                
                # Format the selected slot for display
                date_str = start_time.strftime("%A, %B %d, %Y")
                start_time_str = start_time.strftime("%I:%M %p")
                end_time_str = end_time.strftime("%I:%M %p")
                
                return (f"You've selected: {date_str} from {start_time_str} to {end_time_str}\n\n"
                       f"Please confirm by replying 'yes' or 'no'.")
                
            except ValueError:
                # Show the slots if the user didn't provide a valid number
                slot_options = "I found the following available interview slots:\n\n"
                for i, (start, end) in enumerate(mock_slots[:5], 1):
                    date_str = start.strftime("%A, %B %d, %Y")
                    start_time_str = start.strftime("%I:%M %p")
                    end_time_str = end.strftime("%I:%M %p")
                    slot_options += f"{i}. {date_str} from {start_time_str} to {end_time_str}\n"
                
                slot_options += "\nPlease reply with the number of your preferred slot (e.g., '1', '2', etc.)."
                
                # Update context with the slots and candidate information
                context = {
                    'candidate_id': candidate.id,
                    'recruiter_id': recruiter.id,
                    'name': candidate.name,
                    'email': candidate.email,  # Use actual email from database
                    'position': candidate.position_applied
                }
                
                print(f"Using email from database: {candidate.email}")
                
                self.scheduling_service.update_conversation_state(
                    phone_number, 
                    'awaiting_slot_selection',
                    context
                )
                
                return slot_options
                
        except Exception as e:
            # Log the error and return a friendly message
            print(f"Error in handle_slot_selection_state: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, there was an error processing your selection. Please try again or contact support."
    
    def handle_confirmation_state(self, phone_number, message_body, state):
        """Handle awaiting confirmation state"""
        try:
            # Debug logging
            print(f"Phone number: {phone_number}")
            print(f"Current state: {state.current_state}")
            print(f"Message body: '{message_body}'")
            print(f"Context: {state.context}")
            
            response = message_body.strip().lower()
            
            # Get context
            context = state.context if state.context is not None else {}
            
            # Force read the context from the database to ensure we have the most recent version
            from app.models.database import db
            from app.models.models import ConversationState
            db_state = ConversationState.query.filter_by(phone_number=phone_number).first()
            if db_state and db_state.context:
                # Update missing fields in our context from the database context
                for key, value in db_state.context.items():
                    if key not in context:
                        context[key] = value
                        print(f"Updated {key} from database context: {value}")
            
            if response in ['yes', 'y', 'confirm', 'ok']:
                # Find candidate - get the most recent one with this phone number
                from app.models.models import Candidate
                candidate = Candidate.query.filter_by(phone_number=phone_number).order_by(Candidate.created_at.desc()).first()
                
                if not candidate:
                    print("No candidate found for phone number")
                    return "I'm sorry, there was an error with your registration. Please start over by sending 'hi' or 'hello'."
                
                # Find recruiter
                from app.models.models import Recruiter
                recruiter = Recruiter.query.first()
                
                if not recruiter:
                    print("No recruiters found in database")
                    return "I'm sorry, there are no recruiters available at the moment. Please try again later."
                
                # Get selected slot from context
                selected_slot = context.get('selected_slot')
                
                if not selected_slot:
                    print("No selected slot found in context")
                    return "I'm sorry, there was an error with your scheduling. Please start over by sending 'hi' or 'hello'."
                
                try:
                    # Parse the selected slot
                    start_time = datetime.fromisoformat(selected_slot[0])
                    end_time = datetime.fromisoformat(selected_slot[1])
                    
                    # Get the email from the context, prioritizing it over the database
                    email_to_use = context.get('email')
                    if not email_to_use:
                        email_to_use = candidate.email
                        print(f"Email not found in context, using candidate email from database: {email_to_use}")
                    else:
                        print(f"Using email from context: {email_to_use}")
                    
                    print(f"Scheduling interview for: {start_time} - {end_time}")
                    
                    # Schedule the interview
                    try:
                        # Create the interview record in the database
                        from app.models.models import Interview
                        
                        # Create the interview
                        interview = Interview(
                            start_time=start_time,
                            end_time=end_time,
                            status='scheduled',
                            candidate_id=candidate.id,
                            recruiter_id=recruiter.id
                        )
                        
                        db.session.add(interview)
                        db.session.commit()
                        
                        print(f"Interview scheduled: {interview.id}")
                        
                        # Create calendar event automatically
                        from app.services.google_calendar import GoogleCalendarService
                        calendar_service = GoogleCalendarService()
                        
                        # Create event summary and description
                        event_summary = f"Interview: {candidate.name} for {candidate.position_applied}"
                        event_description = f"Interview with {candidate.name} for the {candidate.position_applied} position."
                        
                        # Create attendees list
                        attendees = [
                            {'email': email_to_use},  # Use candidate email
                            {'email': recruiter.email}  # Use recruiter email
                        ]
                        
                        # Create the calendar event
                        try:
                            event = calendar_service.create_event(
                                recruiter.calendar_id or 'primary',
                                event_summary,
                                event_description,
                                start_time,
                                end_time,
                                attendees
                            )
                            
                            # Update the interview with the calendar event ID
                            interview.calendar_event_id = event.get('id')
                            db.session.commit()
                            
                            print(f"Calendar event created automatically: {event.get('id')}")
                            
                            # Check if there's a Google Meet link
                            meet_link = event.get('hangoutLink')
                            if meet_link:
                                calendar_success_msg = f" A calendar invitation and Google Meet link have been sent to your email."
                            else:
                                calendar_success_msg = " A calendar invitation has been sent to your email."
                        except Exception as e:
                            print(f"Error creating calendar event: {e}")
                            import traceback
                            traceback.print_exc()
                            # Continue even if calendar creation fails
                            calendar_success_msg = " We'll send you a calendar invitation shortly."
                        
                        # Reset the conversation state only after successful interview scheduling
                        self.scheduling_service.update_conversation_state(phone_number, 'initial', {})
                        
                        return ("Great! Your interview has been scheduled." + calendar_success_msg + "\n\n" +
                               "If you need to reschedule, please start over by sending 'hi' or 'hello'.")
                    except Exception as e:
                        print(f"Error scheduling interview: {e}")
                        import traceback
                        traceback.print_exc()
                        return "I'm sorry, there was an error scheduling your interview. Please try again later."
                except Exception as e:
                    print(f"Error parsing selected slot: {e}")
                    return "I'm sorry, there was an error with your scheduling. Please start over by sending 'hi' or 'hello'."
                
            elif response in ['no', 'n', 'cancel']:
                # Go back to availability state
                self.scheduling_service.update_conversation_state(
                    phone_number, 
                    'awaiting_availability',
                    context
                )
                
                return ("No problem! Let's try again. Please share your availability for the interview.\n\n"
                       "Please format your availability as follows:\n"
                       "day time-time, day time-time\n\n"
                       "For example: Monday 2pm-4pm, Tuesday 10am-12pm")
                
            else:
                return "Please confirm by replying 'yes' or 'no'."
        except Exception as e:
            # Log the error and return a friendly message
            print(f"Error in handle_confirmation_state: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, there was an error processing your confirmation. Please try again or contact support." 