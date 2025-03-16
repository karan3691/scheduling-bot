from datetime import datetime
from app.models.database import db

class Candidate(db.Model):
    """Model for candidate information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    position_applied = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with interview slots
    availability_slots = db.relationship('AvailabilitySlot', backref='candidate', lazy=True)
    interviews = db.relationship('Interview', backref='candidate', lazy=True)
    
    def __repr__(self):
        return f'<Candidate {self.name}>'

class Recruiter(db.Model):
    """Model for recruiter information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    calendar_id = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with interview slots
    availability_slots = db.relationship('AvailabilitySlot', backref='recruiter', lazy=True)
    interviews = db.relationship('Interview', backref='recruiter', lazy=True)
    
    def __repr__(self):
        return f'<Recruiter {self.name}>'

class AvailabilitySlot(db.Model):
    """Model for availability slots"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    # Foreign keys
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AvailabilitySlot {self.start_time} - {self.end_time}>'

class Interview(db.Model):
    """Model for scheduled interviews"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, completed, cancelled
    calendar_event_id = db.Column(db.String(200))
    
    # Foreign keys
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Interview {self.start_time} - {self.end_time}>'

class ConversationState(db.Model):
    """Model to track conversation state with candidates"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    current_state = db.Column(db.String(50), default='initial')
    context = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConversationState {self.phone_number}: {self.current_state}>' 