"""
Vercel entry point - Works with Streamlit.
"""
import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create a simple response
def handler(request=None):
    """Vercel serverless function handler."""
    try:
        # Import Streamlit
        import streamlit as st
        
        # Import your main app
        from dashboard.app import main
        
        # Run the app
        return main()
    except Exception as e:
        # Return error as JSON
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

# For Vercel, expose the app
app = handler