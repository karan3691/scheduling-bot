import os
from dotenv import load_dotenv
import pip
from app import create_app

# Check if python-dateutil is installed
try:
    import dateutil
except ImportError:
    pip.main(['install', 'python-dateutil'])

# Load environment variables
load_dotenv()

# Set environment variable for OAuth to work in development
# WARNING: This should only be used in development environments, not in production!
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development') 