"""
Vercel API entry point - Works with serverless functions.
"""
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(request):
    """
    Vercel handler that runs the Streamlit app.
    """
    try:
        # Import Streamlit
        import streamlit.web.cli as stcli
        
        # Set up the command
        sys.argv = [
            "streamlit",
            "run",
            "dashboard/app.py",
            "--server.port=8501",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--browser.gatherUsageStats=false"
        ]
        
        # Run Streamlit
        return stcli.main()
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }