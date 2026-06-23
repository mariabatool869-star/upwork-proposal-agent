"""
Resolve configuration for local dev (config.py) or Streamlit Cloud (project_config.py).
"""

from types import ModuleType


def load_config() -> ModuleType:
    try:
        import config

        return config
    except ImportError:
        import project_config

        project_config.apply_streamlit_secrets()
        return project_config
