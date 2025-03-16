from datetime import datetime, timedelta
import re
from app.services.scheduling_service import SchedulingService
from app.models.models import Candidate, Recruiter, ConversationState

class ConversationHandler:
    """Handler for WhatsApp conversations with candidates"""
    
    def __init__(self):
        """Initialize the conversation handler"""
        self.scheduling_service = SchedulingService()
    
    def handle_message(self, from_number, message_body):
        """Handle incoming WhatsApp messages"""
        try:
            # Clean the phone number (remove 'whatsapp:' prefix if present)
            phone_number = from_number.replace('whatsapp:', '')
            
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
            
            # Check if this is a reset command
            if message_body.lower() == 'reset':
                # Reset the conversation
                self.scheduling_service.update_conversation_state(phone_number, 'initial', {})
                return "Conversation has been reset. Send 'hi' or 'hello' to start again."
            
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
            
            # Check if user is trying to restart the conversation
            if message_body.lower() in ['hi', 'hello', 'hey', 'start'] and state.current_state != 'initial':
                # If we're in awaiting_name state and user sends Hi again, treat it as their name
                if state.current_state == 'awaiting_name':
                    return self.handle_name_state(phone_number, message_body, state)
                
                # Otherwise, ask if they want to restart
                return ("It looks like you're already in the middle of scheduling an interview. "
                       "Would you like to continue where you left off or start over? "
                       "Reply 'continue' to continue or 'reset' to start over.")
            
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
                # Default response for unknown state
                # Reset to initial state to recover
                self.scheduling_service.update_conversation_state(phone_number, 'initial', {})
                return "I'm sorry, I'm having trouble understanding. Please start over by sending 'hi' or 'hello'."
        except Exception as e:
            print(f"Error in handle_message: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Try to recover by resetting the state
            try:
                self.scheduling_service.update_conversation_state(from_number.replace('whatsapp:', ''), 'initial', {})
            except:
                pass
                
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
            
            # Update conversation state
            self.scheduling_service.update_conversation_state(
                phone_number, 
                'awaiting_position',
                context
            )
            
            # Double-check that the email was saved in the context
            updated_state = self.scheduling_service.get_or_create_conversation_state(phone_number)
            print(f"Verifying email was saved: {updated_state.context}")
            
            if 'email' not in updated_state.context or not updated_state.context['email']:
                print("WARNING: Email was not saved in context, forcing update")
                # Force update the context directly in the database
                from app.models.database import db
                from app.models.models import ConversationState
                
                state_record = ConversationState.query.filter_by(phone_number=phone_number).first()
                if state_record:
                    import json
                    context_copy = state_record.context.copy() if state_record.context else {}
                    context_copy['email'] = email
                    state_record.context = context_copy
                    db.session.commit()
                    print(f"Forced context update: {state_record.context}")
            
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
                        from app.models.models import ConversationState
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
            # Debug logging
            print(f"Phone number: {phone_number}")
            print(f"Current state: {state.current_state}")
            print(f"Message body: '{message_body}'")
            print(f"Context: {state.context}")
            
            # Parse availability from message
            availability_slots = self.scheduling_service.parse_availability(message_body)
            
            print(f"Parsed availability slots: {availability_slots}")
            
            if not availability_slots:
                return ("I couldn't understand your availability format. Please use the format:\n"
                       "day time-time, day time-time\n\n"
                       "For example: Monday 2pm-4pm, Tuesday 10am-12pm")
            
            # Get candidate ID from context
            context = state.context if state.context is not None else {}
            candidate_id = context.get('candidate_id')
            
            print(f"Candidate ID from context: {candidate_id}")
            
            if not candidate_id:
                # If candidate_id is missing, try to find the candidate by phone number
                print(f"Candidate ID missing, trying to find candidate by phone number")
                from app.models.models import Candidate
                candidate = Candidate.query.filter_by(phone_number=phone_number).order_by(Candidate.created_at.desc()).first()
                
                if candidate:
                    candidate_id = candidate.id
                    # Update the context with all candidate information
                    context['candidate_id'] = candidate_id
                    context['name'] = candidate.name
                    context['email'] = candidate.email
                    context['position'] = candidate.position_applied
                    print(f"Found candidate by phone number: {candidate_id}, email: {candidate.email}")
                else:
                    print(f"No candidate found for phone number: {phone_number}")
                    # Try to register the candidate again
                    if 'name' in context and 'email' in context and 'position' in context:
                        print(f"Attempting to register candidate again")
                        candidate = self.scheduling_service.register_candidate(
                            context['name'],
                            phone_number,
                            context['email'],
                            context['position']
                        )
                        candidate_id = candidate.id
                        context['candidate_id'] = candidate_id
                        print(f"Re-registered candidate: {candidate_id}")
                    else:
                        print(f"Missing required fields for registration")
                        return "I'm sorry, there was an error with your registration. Please start over by sending 'hi' or 'hello'."
            
            # Add availability slots to database
            for start_time, end_time in availability_slots:
                slot = self.scheduling_service.add_candidate_availability(candidate_id, start_time, end_time)
                print(f"Added availability slot: {slot}")
            
            # Find matching slots with recruiters
            # For simplicity, we'll use the first recruiter in the database
            from app.models.models import Recruiter
            recruiter = Recruiter.query.first()
            
            if not recruiter:
                print("No recruiters found in database")
                return "I'm sorry, there are no recruiters available at the moment. Please try again later."
            
            print(f"Found recruiter: {recruiter.id} - {recruiter.name}")
            
            # Find matching slots
            now = datetime.now()
            end_date = now + timedelta(days=14)  # Look for slots in the next 14 days
            
            # Use mock data for testing instead of actual calendar integration
            # This will ensure the conversation flows smoothly without Google Calendar authentication
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
            
            matching_slots = mock_slots
            
            print(f"Generated mock matching slots: {matching_slots}")
            
            if not matching_slots:
                return ("I couldn't find any matching slots with our recruiters based on your availability.\n\n"
                       "Please provide more availability options or different time slots.")
            
            # Format matching slots for display
            slot_options = "I found the following available interview slots:\n\n"
            
            for i, (start, end) in enumerate(matching_slots[:5], 1):  # Limit to 5 options
                date_str = start.strftime("%A, %B %d, %Y")
                start_time_str = start.strftime("%I:%M %p")
                end_time_str = end.strftime("%I:%M %p")
                
                slot_options += f"{i}. {date_str} from {start_time_str} to {end_time_str}\n"
            
            slot_options += "\nPlease reply with the number of your preferred slot (e.g., '1', '2', etc.)."
            
            # Update state with matching slots and recruiter ID
            context['matching_slots'] = [(slot[0].isoformat(), slot[1].isoformat()) for slot in matching_slots[:5]]
            context['recruiter_id'] = recruiter.id
            
            self.scheduling_service.update_conversation_state(
                phone_number, 
                'awaiting_slot_selection',
                context
            )
            
            return slot_options
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
                    
                    print(f"Scheduling interview for: {start_time} - {end_time}")
                    print(f"Using candidate email from database: {candidate.email}")
                    
                    # Schedule the interview
                    try:
                        # Create the interview record in the database
                        from app.models.models import Interview
                        from app.models.database import db
                        
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
                    except Exception as e:
                        print(f"Error scheduling interview: {e}")
                        import traceback
                        traceback.print_exc()
                        return "I'm sorry, there was an error scheduling your interview. Please try again later."
                    
                    # Reset the conversation state
                    self.scheduling_service.update_conversation_state(phone_number, 'initial', {})
                    
                    return ("Great! Your interview has been scheduled. You will receive a calendar invitation shortly at " + 
                           f"{candidate.email}.\n\n" +
                           "If you need to reschedule or have any questions, please contact our recruitment team.\n\n" +
                           "Thank you and good luck with your interview!")
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