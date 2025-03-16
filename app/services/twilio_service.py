import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TwilioService:
    """Service for interacting with Twilio API for WhatsApp messaging"""
    
    def __init__(self):
        """Initialize the Twilio client"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_whatsapp_message(self, to_number, message):
        """Send a WhatsApp message using Twilio"""
        # Format the 'to' number for WhatsApp
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Format the 'from' number for WhatsApp
        from_number = f'whatsapp:{self.phone_number}'
        
        # Send the message
        message = self.client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        return message.sid
    
    def send_template_message(self, to_number, template_name, template_data=None):
        """Send a WhatsApp template message using Twilio"""
        # Format the 'to' number for WhatsApp
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Format the 'from' number for WhatsApp
        from_number = f'whatsapp:{self.phone_number}'
        
        # Prepare the content SID
        content_sid = os.getenv('TWILIO_CONTENT_SID')
        
        # Send the template message
        message = self.client.messages.create(
            content_sid=content_sid,
            from_=from_number,
            to=to_number,
            content_variables=template_data
        )
        
        return message.sid 