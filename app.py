"""
Vercel entry point for Streamlit app.
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def handler(request):
    """
    Vercel serverless function handler.
    This is REQUIRED for Vercel deployment.
    """
    try:
        # Import and run Streamlit app
        import streamlit.web.cli as stcli
        import sys
        
        # Set up Streamlit args
        sys.argv = [
            "streamlit",
            "run",
            "dashboard/app.py",
            "--server.port=8501",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
            "--server.address=0.0.0.0"
        ]
        
        # Run Streamlit
        return stcli.main()
    except Exception as e:
        return f"Error: {str(e)}"

# For local testing
if __name__ == "__main__":
    from dashboard.app import main
    main()