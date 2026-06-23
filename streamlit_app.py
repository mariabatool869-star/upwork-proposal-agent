"""
Streamlit Community Cloud entry point.
Deploy at: https://share.streamlit.io
Main file: streamlit_app.py

Local:  python -m streamlit run streamlit_app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dashboard"))

try:
    import config
except ImportError:
    import project_config as config

sys.modules["config"] = config

import app  # noqa: F401 — loads dashboard/app.py
