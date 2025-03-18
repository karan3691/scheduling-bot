from flask import Blueprint, request, Response, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from app.services.conversation_handler import ConversationHandler

# Create blueprint
webhook_bp = Blueprint('webhook', __name__)

# Initialize conversation handler
conversation_handler = ConversationHandler()

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming messages (both Twilio and JSON formats)"""
    try:
        # Check if the request is JSON
        if request.is_json:
            data = request.get_json()
            from_number = data.get('from', '')
            body = data.get('message', '')
        else:
            # Handle Twilio format
            from_number = request.values.get('From', '')
            body = request.values.get('Body', '')
        
        print(f"Received message from {from_number}: '{body}'")
        
        # Handle the message
        response_text = conversation_handler.handle_message(from_number, body)
        
        # If it's a JSON request, return JSON response
        if request.is_json:
            return jsonify({
                'response': response_text,
                'from': from_number
            })
        
        # Otherwise, return Twilio response
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
        error_message = "I'm sorry, there was an error processing your message. Please try again by sending 'hi' or 'hello'."
        
        if request.is_json:
            return jsonify({
                'response': error_message,
                'error': str(e)
            })
        
        resp = MessagingResponse()
        resp.message(error_message)
        return Response(str(resp), mimetype='text/xml') 