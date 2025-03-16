import os
from dotenv import load_dotenv
from app.services.twilio_service import TwilioService

# Load environment variables
load_dotenv()

def test_twilio():
    """Test Twilio WhatsApp integration"""
    # Initialize Twilio service
    twilio_service = TwilioService()
    
    # Get phone number from user input
    phone_number = input("Enter your WhatsApp phone number (with country code, e.g., +1234567890): ")
    
    # Send a test message
    message = "Hello! This is a test message from the AI-Powered Scheduling Bot."
    
    try:
        message_sid = twilio_service.send_whatsapp_message(phone_number, message)
        print(f"Message sent successfully! SID: {message_sid}")
    except Exception as e:
        print(f"Error sending message: {str(e)}")

if __name__ == '__main__':
    test_twilio() 