"""
Streamlit Cloud entry point.

In Streamlit Cloud set Main file path to: streamlit_app.py
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import runs the dashboard UI defined in dashboard/app.py
import dashboard.app  # noqa: F401
