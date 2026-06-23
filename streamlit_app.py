"""
Streamlit Community Cloud entry point.
Deploy main file: streamlit_app.py (same GitHub → deploy flow as Vercel).

Local run:
  python -m streamlit run streamlit_app.py
"""
import runpy
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

runpy.run_path(str(ROOT / "dashboard" / "app.py"), run_name="__main__")
