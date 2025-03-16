# Interview Scheduling Bot

## BasisVectors Hackathon Project

![Scheduling Bot Logo](https://via.placeholder.com/150?text=SchedulingBot)

## 🏆 Hackathon Challenge Solution

This project was developed for the BasisVectors Hackathon, addressing the challenge of streamlining the interview scheduling process. Our solution automates the entire workflow from initial candidate contact to calendar invitation, saving recruiters countless hours and improving candidate experience.

## 📊 Presentation for Submission

As part of the BasisVectors Hackathon requirements, a presentation (PowerPoint/slides) must be submitted alongside the working solution. The presentation should include:

1. **Problem Statement**: The inefficiency of traditional interview scheduling processes
2. **Solution Overview**: How our WhatsApp bot addresses these challenges
3. **Key Features**: Highlighting the main capabilities of our solution
4. **Technical Architecture**: Simplified diagrams of how the system works
5. **Demo Screenshots**: Visual examples of the bot in action
6. **Implementation Details**: Brief overview of technologies used
7. **Challenges & Solutions**: Problems encountered and how we solved them
8. **Future Enhancements**: How the solution could be improved further
9. **Team Information**: Contributors and their roles

The presentation should be concise (10-15 slides) but comprehensive, focusing on both the technical implementation and the business value of the solution.

**[Link to Presentation](presentation.pdf)**

## 💡 Hackathon Challenge Highlights

### The Challenge
The BasisVectors Hackathon challenged us to solve a critical problem in the recruitment process: the inefficient and time-consuming nature of interview scheduling. Recruiters spend hours coordinating with candidates through multiple back-and-forth communications, leading to delays, errors, and poor candidate experience.

### Our Solution at a Glance
We built an AI-powered WhatsApp bot that revolutionizes the interview scheduling process by:
- Automating candidate interactions through natural language conversations
- Intelligently parsing availability preferences
- Seamlessly integrating with Google Calendar
- Providing a comprehensive admin dashboard for recruiters

### Key Features & User Experience
- **Conversational AI Interface**: Candidates interact with a friendly, intuitive WhatsApp bot that feels like texting a human recruiter
- **Seamless Scheduling Flow**: From initial greeting to calendar invitation in minutes, not days
- **Context-Aware Conversations**: The bot remembers user information and maintains conversation context
- **Error-Tolerant Interactions**: Intelligent handling of unexpected inputs with helpful guidance
- **Real-Time Calendar Integration**: Automatic checking of availability and instant scheduling
- **Admin Control Center**: Comprehensive dashboard for recruiters to manage the entire process

### Core Components Breakdown
1. **Conversation Management System**
   - State machine architecture for tracking conversation progress
   - Context preservation across multiple messages
   - Natural language understanding for intent recognition

2. **Availability Parser**
   - Custom NLP engine for interpreting time expressions (e.g., "Monday afternoon between 2-4pm")
   - Validation logic to ensure parsed times are valid
   - Conversion of natural language to structured datetime objects

3. **Calendar Integration**
   - OAuth2 authentication with Google Calendar
   - Automatic slot generation based on availability
   - Calendar event creation with proper metadata
   - Email notification system for calendar invitations

4. **Database Architecture**
   - Relational schema for candidate, recruiter, and interview data
   - Conversation state persistence
   - Transaction management for data integrity

5. **Admin Interface**
   - Real-time dashboard for interview monitoring
   - Calendar connection management
   - Candidate information access
   - Interview status tracking

### Technical Stack
- **Programming Languages**:
  - Python (Backend logic)
  - HTML/CSS/JavaScript (Frontend dashboard)
  - SQL (Database queries)

- **Frameworks & Libraries**:
  - Flask (Web application framework)
  - SQLAlchemy (ORM for database interactions)
  - Google API Client (Calendar integration)
  - Twilio API (WhatsApp messaging)
  - Jinja2 (Template engine)

- **Database**:
  - SQLite (Development)
  - Relational schema design

- **AI & NLP Components**:
  - Custom NLP logic for parsing availability
  - State machine for conversation flow
  - Context management techniques
  - Pattern recognition for entity extraction

- **Integrations**:
  - Twilio WhatsApp API
  - Google Calendar API
  - Email notification system

- **Deployment**:
  - Containerized application
  - Environment variable configuration
  - Webhook setup for real-time messaging
  - Ngrok for local webhook tunneling

## 📝 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technical Architecture](#technical-architecture)
- [AI & ML Implementation](#ai--ml-implementation)
- [User Flow](#user-flow)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Future Enhancements](#future-enhancements)
- [Challenges & Solutions](#challenges--solutions)
- [Team](#team)
- [License](#license)

## 🔍 Overview

The Interview Scheduling Bot is an AI-powered WhatsApp bot that automates the interview scheduling process. It engages candidates in natural conversation, collects their information, availability preferences, and automatically schedules interviews by integrating with Google Calendar. The system includes an admin dashboard for recruiters to manage interviews and candidates.

### Problem Statement

Scheduling interviews is a time-consuming process that involves multiple back-and-forth communications between recruiters and candidates. This process is prone to errors, miscommunications, and delays, resulting in a poor candidate experience and inefficient use of recruiters' time.

### Our Solution

We've developed an intelligent WhatsApp bot that handles the entire scheduling process, from initial contact to calendar invitation. The bot uses natural language processing to understand candidate availability, integrates with Google Calendar to find suitable slots, and automatically sends calendar invitations to both parties.

## 🌟 Key Features

### Conversational Interface
- **Natural Language Interaction**: Engage with candidates using everyday language
- **Guided Conversation Flow**: Step-by-step guidance through the scheduling process
- **Context Awareness**: Maintains conversation context across multiple messages
- **Error Recovery**: Intelligent handling of unexpected inputs with helpful prompts

### Intelligent Scheduling
- **Availability Parsing**: Understands natural language time expressions (e.g., "Monday 2pm-4pm")
- **Smart Slot Generation**: Creates appropriate interview slots based on availability
- **Calendar Integration**: Connects with Google Calendar for real-time availability checking
- **Automated Invitations**: Sends calendar invitations to all participants

### Admin Dashboard
- **Interview Management**: View, manage, and track all scheduled interviews
- **Candidate Management**: Access candidate information and history
- **Calendar Controls**: Connect/disconnect Google Calendar integration
- **Status Tracking**: Monitor interview status (scheduled, completed, cancelled)
- **Calendar Event Creation**: Create calendar events directly from the dashboard

### Multi-User Support
- **Unique Candidate Tracking**: Maintains separate records for each candidate
- **Shared Phone Number Support**: Works correctly even when multiple users share a device
- **Conversation State Management**: Keeps track of where each user is in the process

## 🏗️ Technical Architecture

### High-Level Architecture
The application follows a service-oriented architecture with clear separation of concerns:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  WhatsApp API   │────▶│  Flask Backend  │────▶│  Google Calendar│
│  (Twilio)       │     │  (Python)       │     │  API            │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │  SQLite Database│
                        │                 │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │  Admin Dashboard│
                        │  (Flask/Jinja)  │
                        │                 │
                        └─────────────────┘
```

### Core Components

#### 1. Conversation Management System
- **State Machine**: Tracks conversation progress through defined states
- **Context Management**: Stores and retrieves user information throughout the conversation
- **Message Handling**: Processes incoming messages and generates appropriate responses

#### 2. Natural Language Processing
- **Intent Recognition**: Identifies user intentions from message content
- **Entity Extraction**: Pulls out key information like names, emails, and times
- **Availability Parsing**: Converts natural language time expressions into structured data

#### 3. Calendar Integration
- **Google Calendar API**: Connects to users' calendars for availability checking
- **OAuth Authentication**: Secure connection to Google services
- **Event Creation**: Automatically creates calendar events for interviews

#### 4. Database System
- **Candidate Storage**: Maintains records of all candidates and their information
- **Interview Tracking**: Stores details of all scheduled interviews
- **Conversation State Persistence**: Saves conversation state between messages

#### 5. Admin Interface
- **Dashboard**: Provides overview of scheduling activity
- **Interview Management**: Tools for viewing and managing interviews
- **Calendar Configuration**: Interface for connecting Google Calendar

### Design Patterns Used
- **Model-View-Controller (MVC)**: Separates data, presentation, and control logic
- **Service-Oriented Architecture**: Modular services with clear responsibilities
- **State Machine Pattern**: For conversation flow management
- **Repository Pattern**: For data access abstraction
- **Dependency Injection**: For service composition

## 🧠 AI & ML Implementation

### Natural Language Processing
- **Custom NLP Logic**: Hand-crafted rules for parsing availability
- **Pattern Recognition**: For identifying dates, times, and commands
- **Context Management**: AI techniques for maintaining conversation context

### Conversation Flow
- **State-based Dialogue Management**: Tracks conversation progress and guides users
- **Error Handling**: Intelligent recovery from unexpected inputs
- **Context Preservation**: Maintains conversation context across multiple messages

### Time and Date Parsing
- **Natural Language Time Understanding**: Converts expressions like "Monday 2pm-4pm" into structured datetime objects
- **Validation Logic**: Ensures parsed times are valid and within acceptable ranges
- **Fuzzy Matching**: Handles variations in time format specifications

## 👤 User Flow

### Candidate Experience
1. **Initial Contact**: Candidate messages the WhatsApp number
2. **Information Collection**: Bot collects name, email, and position
3. **Availability Sharing**: Candidate shares their availability in natural language
4. **Slot Selection**: Bot presents available slots and candidate selects one
5. **Confirmation**: Candidate confirms the selected slot
6. **Calendar Invitation**: Candidate receives a calendar invitation via email

### Recruiter Experience
1. **Dashboard Access**: Recruiter logs into the admin dashboard
2. **Interview Overview**: Views all scheduled interviews
3. **Calendar Connection**: Connects their Google Calendar
4. **Interview Management**: Views, manages, and tracks interview status
5. **Calendar Integration**: Interviews appear on their Google Calendar

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Flask
- SQLAlchemy
- Google API Client Library
- Twilio API Client
- A Twilio account with WhatsApp integration
- A Google account with Calendar API access

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/scheduling-bot.git
   cd scheduling-bot
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Set up environment variables**
   Create a `.env` file with the following variables:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_whatsapp_number
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Set up Twilio webhook**
   - In your Twilio console, set the WhatsApp webhook URL to `https://your-domain.com/webhook`
   - For local development, use ngrok to expose your local server:
     ```bash
     ngrok http 8080  # Replace 8080 with your application port
     ```
   - Copy the HTTPS URL provided by ngrok (e.g., https://a1b2c3d4.ngrok.io)
   - Set this URL + "/webhook" as your Twilio WhatsApp webhook URL
   - Ngrok URLs change each time you restart ngrok unless you have a paid account

## ⚙️ Configuration

### Google Calendar API Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials
5. Download the client secret JSON file and save it as `client-secret.json` in the project root

### Twilio WhatsApp Setup
1. Sign up for a Twilio account
2. Activate the WhatsApp sandbox
3. Configure the webhook URL to point to your `/webhook` endpoint:
   - For production: Use your domain (https://your-domain.com/webhook)
   - For development: Use ngrok to create a secure tunnel to your local server
     ```bash
     ngrok http 8080  # Replace 8080 with your application port
     ```
4. In the Twilio console, set the webhook URL to your ngrok HTTPS URL + "/webhook"
5. Test the connection by sending a message to your Twilio WhatsApp number

### Admin Dashboard Access
1. The admin dashboard is available at `/admin`
2. Default credentials are created during database initialization
3. Connect your Google Calendar by clicking "Connect Google Calendar" in the dashboard

## 📱 Usage Guide

### For Candidates
1. Send "hi" or "hello" to the WhatsApp number
2. Follow the bot's prompts to provide your information
3. Share your availability in natural language (e.g., "Monday 2pm-4pm, Tuesday 10am-12pm")
4. Select an available slot by replying with the number
5. Confirm your selection by replying "yes"
6. Check your email for the calendar invitation

### For Recruiters
1. Log in to the admin dashboard
2. Connect your Google Calendar
3. View scheduled interviews on the dashboard
4. Click on an interview to see details
5. Use the dashboard to manage interviews (mark as completed, cancel, etc.)
6. Create calendar events for interviews that don't have them

## 📚 API Documentation

### Webhook Endpoint
- **URL**: `/webhook`
- **Method**: POST
- **Description**: Receives WhatsApp messages from Twilio
- **Parameters**:
  - `From`: The sender's WhatsApp number
  - `Body`: The message content

### Admin API Endpoints
- **GET** `/admin/`: Admin dashboard
- **GET** `/admin/interviews`: List all interviews
- **GET/POST** `/admin/interviews/<id>`: View/update interview details
- **GET** `/admin/candidates`: List all candidates
- **GET** `/admin/recruiters`: List all recruiters
- **GET/POST** `/admin/recruiters/add`: Add a new recruiter

### Google Calendar API Integration
- **GET** `/authorize`: Start OAuth flow
- **GET** `/oauth2callback`: Handle OAuth callback
- **GET** `/revoke`: Revoke calendar access

## 🚀 Future Enhancements

### Short-term Improvements
1. **Enhanced NLP**: Integrate with a more sophisticated NLP service
2. **Multi-language Support**: Add support for multiple languages
3. **SMS Fallback**: Add SMS support for users without WhatsApp
4. **Customizable Templates**: Allow recruiters to customize message templates

### Long-term Vision
1. **AI-powered Scheduling Optimization**: Use machine learning to optimize interview scheduling
2. **Integration with ATS Systems**: Connect with Applicant Tracking Systems
3. **Candidate Feedback Collection**: Collect feedback after interviews
4. **Analytics Dashboard**: Provide insights on scheduling patterns and efficiency
5. **Mobile App**: Develop a mobile app for recruiters

## 🧩 Challenges & Solutions

### Challenge 1: Maintaining Conversation Context
**Problem**: WhatsApp messages are stateless, making it difficult to maintain conversation context.
**Solution**: Implemented a robust state management system using a database to track conversation state and context.

### Challenge 2: Natural Language Time Parsing
**Problem**: Understanding various formats of time expressions in natural language.
**Solution**: Developed a custom time parsing system that can handle different formats and variations.

### Challenge 3: Google Calendar Integration
**Problem**: OAuth flow requires HTTPS, which is challenging in development environments.
**Solution**: Implemented a development mode that allows OAuth to work with HTTP for testing, with clear warnings about production security.

### Challenge 4: Multiple Users with Same Phone
**Problem**: Multiple candidates using the same phone number caused data conflicts.
**Solution**: Modified the database schema and conversation handling to support multiple candidates with the same phone number.

## 👥 Team

- **Karan Sahota** - Full Stack Developer & Project Lead (Primary Contributor)
- **Pratham Malviya** - Documentation & Testing
- **S Praneeth Nanabolu** - UI/UX Design Support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- BasisVectors for organizing the hackathon
- Twilio for the WhatsApp API
- Google for the Calendar API
- All the mentors and judges who provided guidance and feedback

---

*This project was created during the BasisVectors Hackathon 2025.* 