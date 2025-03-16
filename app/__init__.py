import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from app.models.database import db
from app.routes.webhook import webhook_bp
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure the SQLAlchemy database
    database_url = os.getenv('DATABASE_URL')
    # If DATABASE_URL is not set or doesn't start with sqlite, use a default SQLite database
    if not database_url or not database_url.startswith('sqlite'):
        database_url = 'sqlite:///scheduling_bot.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.urandom(24)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(webhook_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    
    # Add a root route to redirect to admin dashboard
    @app.route('/')
    def index():
        """Redirect to admin dashboard"""
        return redirect(url_for('admin.dashboard'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
