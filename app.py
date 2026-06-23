"""
Vercel entry point - Runs the Streamlit dashboard.
"""
import streamlit as st
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the dashboard app
from dashboard.app import main

if __name__ == "__main__":
    main()

# ============================================================
# VERCEL HANDLER (REQUIRED)
# ============================================================

def handler(request):
    """Vercel serverless function handler."""
    return main()