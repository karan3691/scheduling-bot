from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.database import db
from app.models.models import Candidate, Recruiter, Interview
from app.services.scheduling_service import SchedulingService
from app.services.google_calendar import GoogleCalendarService

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Initialize scheduling service
scheduling_service = SchedulingService()

@admin_bp.route('/')
def dashboard():
    """Admin dashboard"""
    # Get counts
    candidate_count = Candidate.query.count()
    recruiter_count = Recruiter.query.count()
    interview_count = Interview.query.count()
    
    # Get recent interviews
    recent_interviews = Interview.query.order_by(Interview.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        candidate_count=candidate_count,
        recruiter_count=recruiter_count,
        interview_count=interview_count,
        recent_interviews=recent_interviews
    )

@admin_bp.route('/recruiters')
def recruiters():
    """List all recruiters"""
    recruiters = Recruiter.query.all()
    return render_template('admin/recruiters.html', recruiters=recruiters)

@admin_bp.route('/recruiters/add', methods=['GET', 'POST'])
def add_recruiter():
    """Add a new recruiter"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        calendar_id = request.form.get('calendar_id')
        
        if not name or not email:
            flash('Name and email are required', 'error')
            return redirect(url_for('admin.add_recruiter'))
        
        # Register recruiter
        recruiter = scheduling_service.register_recruiter(name, email, calendar_id)
        
        flash(f'Recruiter {name} added successfully', 'success')
        return redirect(url_for('admin.recruiters'))
    
    return render_template('admin/add_recruiter.html')

@admin_bp.route('/recruiters/edit/<int:recruiter_id>', methods=['GET', 'POST'])
def edit_recruiter(recruiter_id):
    """Edit a recruiter"""
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        calendar_id = request.form.get('calendar_id')
        
        if not name or not email:
            flash('Name and email are required', 'error')
            return redirect(url_for('admin.edit_recruiter', recruiter_id=recruiter_id))
        
        # Update recruiter
        recruiter.name = name
        recruiter.email = email
        recruiter.calendar_id = calendar_id
        
        db.session.commit()
        
        flash(f'Recruiter {name} updated successfully', 'success')
        return redirect(url_for('admin.recruiters'))
    
    return render_template('admin/edit_recruiter.html', recruiter=recruiter)

@admin_bp.route('/recruiters/delete/<int:recruiter_id>', methods=['POST'])
def delete_recruiter(recruiter_id):
    """Delete a recruiter"""
    recruiter = Recruiter.query.get_or_404(recruiter_id)
    
    # Delete recruiter
    db.session.delete(recruiter)
    db.session.commit()
    
    flash(f'Recruiter {recruiter.name} deleted successfully', 'success')
    return redirect(url_for('admin.recruiters'))

@admin_bp.route('/candidates')
def candidates():
    """List all candidates"""
    candidates = Candidate.query.all()
    return render_template('admin/candidates.html', candidates=candidates)

@admin_bp.route('/interviews')
def interviews():
    """List all interviews"""
    interviews = Interview.query.order_by(Interview.start_time.desc()).all()
    return render_template('admin/interviews.html', interviews=interviews)

@admin_bp.route('/interviews/<int:interview_id>', methods=['GET', 'POST'])
def interview_details(interview_id):
    """View interview details"""
    interview = Interview.query.get(interview_id)
    
    # If interview doesn't exist, redirect to interviews page with a message
    if not interview:
        flash('Interview not found. It may have been deleted.', 'warning')
        return redirect(url_for('admin.interviews'))
    
    # Set calendar URL if event ID exists
    if interview.calendar_event_id:
        interview.calendar_url = f"https://calendar.google.com/calendar/event?eid={interview.calendar_event_id}"
        db.session.commit()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'complete':
            interview.status = 'completed'
            interview.candidate.status = 'interviewed'
            db.session.commit()
            flash('Interview marked as completed', 'success')
            
        elif action == 'cancel':
            interview.status = 'cancelled'
            
            # Cancel the calendar event
            if interview.calendar_event_id:
                calendar_service = GoogleCalendarService()
                try:
                    # Use 'primary' as default calendar ID if not set
                    calendar_id = interview.recruiter.calendar_id or 'primary'
                    calendar_service.delete_event(
                        calendar_id,
                        interview.calendar_event_id
                    )
                    flash('Interview and calendar event cancelled successfully', 'success')
                except Exception as e:
                    flash(f'Error cancelling calendar event: {str(e)}', 'error')
            
            db.session.commit()
            flash('Interview cancelled', 'success')
        
        elif action == 'create_calendar_event':
            # Create calendar event
            calendar_service = GoogleCalendarService()
            try:
                # Create event summary and description
                event_summary = f"Interview: {interview.candidate.name} for {interview.candidate.position_applied}"
                event_description = f"Interview with {interview.candidate.name} for the {interview.candidate.position_applied} position."
                
                # Create attendees list
                attendees = [
                    {'email': interview.candidate.email, 'responseStatus': 'needsAction'},
                    {'email': interview.recruiter.email, 'responseStatus': 'accepted'}
                ]
                
                # Create the calendar event
                event = calendar_service.create_event(
                    interview.recruiter.calendar_id or 'primary',
                    event_summary,
                    event_description,
                    interview.start_time,
                    interview.end_time,
                    attendees
                )
                
                # Update the interview with the calendar event ID and URL
                interview.calendar_event_id = event.get('id')
                interview.calendar_url = f"https://calendar.google.com/calendar/event?eid={event.get('id')}"
                db.session.commit()
                
                flash('Calendar event created successfully', 'success')
            except Exception as e:
                import traceback
                traceback.print_exc()
                flash(f'Error creating calendar event: {str(e)}', 'error')
        
        return redirect(url_for('admin.interview_details', interview_id=interview.id))
    
    return render_template('admin/interview_details.html', interview=interview) 