import streamlit as st
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the dashboard
from dashboard.app import *

if __name__ == "__main__":
    # The app is already defined in dashboard/app.py
    pass