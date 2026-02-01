import sys
import os

# Add the project root to sys.path so we can import 'app'
# We are in /netlify/functions/api.py, so root is two levels up
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import aws_wsgi
from app import create_app

# Initialize the app
app = create_app()

def handler(event, context):
    """
    Netlify Function Handler
    """
    return aws_wsgi.response(app, event, context)
