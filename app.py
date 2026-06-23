"""
Vercel entry point - Exposes the Streamlit app.
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# This imports the Streamlit app
from dashboard.app import main

# Vercel looks for a variable named "app"
# This is the handler Vercel needs
app = main

# Handler function for Vercel
def handler(request=None):
    """Vercel serverless function handler."""
    return app()