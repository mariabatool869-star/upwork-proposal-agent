"""
Vercel entry point - Streamlit app.
"""
import streamlit as st
import sys
import os

# Add path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual app
from dashboard.app import main

# THIS IS WHAT VERCEL NEEDS
app = main

# This is the handler Vercel expects
def handler(request = None):
    """Vercel serverless function handler."""
    return app()