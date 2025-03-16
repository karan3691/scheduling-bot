from flask import Blueprint, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.conversation_handler import ConversationHandler

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

# Initialize conversation handler
conversation_handler = ConversationHandler()

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages"""
    try:
        # Get incoming message details
        from_number = request.values.get('From', '')
        body = request.values.get('Body', '')
        
        print(f"Received message from {from_number}: '{body}'")
        
        # Handle the message
        response_text = conversation_handler.handle_message(from_number, body)
        
        # Create Twilio response
        resp = MessagingResponse()
        resp.message(response_text)
        
        print(f"Sending response: '{response_text}'")
        
        return Response(str(resp), mimetype='text/xml')
    except Exception as e:
        # Log the error
        import traceback
        print(f"Error in webhook: {str(e)}")
        traceback.print_exc()
        
        # Always send a response even if there's an error
        resp = MessagingResponse()
        resp.message("I'm sorry, there was an error processing your message. Please try again by sending 'hi' or 'hello'.")
        
        return Response(str(resp), mimetype='text/xml') 