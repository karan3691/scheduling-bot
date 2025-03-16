import os
from dotenv import load_dotenv
from app.services.conversation_handler import ConversationHandler

# Load environment variables
load_dotenv()

def test_conversation():
    """Test the conversation flow with the bot"""
    # Initialize conversation handler
    conversation_handler = ConversationHandler()
    
    # Simulate a phone number
    phone_number = input("Enter a test phone number (with country code, e.g., +1234567890): ")
    
    print("\nStarting conversation simulation. Type 'exit' to quit.\n")
    print("Bot: Hello! I'm your interview scheduling assistant. 👋\n"
          "To start scheduling your interview, please send 'hi' or 'hello'.")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            break
        
        # Handle the message
        response = conversation_handler.handle_message(phone_number, user_input)
        
        # Print the bot's response
        print(f"\nBot: {response}")

if __name__ == '__main__':
    test_conversation() 