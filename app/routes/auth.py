import os
import requests
from flask import Blueprint, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# OAuth configuration
CLIENT_SECRETS_FILE = 'client-secret.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_FILE = 'token.pickle'

# Allow OAuth2 to work with HTTP in development environment
# WARNING: This should NEVER be used in production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

@auth_bp.route('/authorize')
def authorize():
    """Start the OAuth flow"""
    # Create flow instance
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('auth.oauth2callback', _external=True)
    )
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Store the state in the session
    session['state'] = state
    
    # Redirect to authorization URL
    return redirect(authorization_url)

@auth_bp.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback"""
    # Verify state
    state = session.get('state')
    
    # Create flow instance
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('auth.oauth2callback', _external=True)
    )
    
    # Exchange authorization code for credentials
    flow.fetch_token(authorization_response=request.url)
    
    # Get credentials
    credentials = flow.credentials
    
    # Save credentials to file
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(credentials, token)
    
    return redirect(url_for('admin.dashboard'))

@auth_bp.route('/revoke')
def revoke():
    """Revoke current credentials"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)
        
        # Build credentials
        credentials = Credentials(
            token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=credentials.scopes
        )
        
        # Revoke credentials
        revoke = requests.post(
            'https://oauth2.googleapis.com/revoke',
            params={'token': credentials.token},
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )
        
        # Delete token file
        os.remove(TOKEN_FILE)
    
    return redirect(url_for('admin.dashboard')) 