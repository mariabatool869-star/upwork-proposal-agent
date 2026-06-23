"""
Simple login for the portfolio dashboard.
Default: demo / demo123 (change in data/users.json or use env).
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERS_FILE = PROJECT_ROOT / "data" / "users.json"


def _init_users():
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text(
            json.dumps(
                {
                    "demo": {
                        "password": hashlib.sha256(b"demo123").hexdigest(),
                        "email": "demo@example.com",
                        "plan": "pro",
                    }
                },
                indent=2,
            )
        )


def check_auth() -> bool:
    return st.session_state.get("logged_in", False)


def login(username: str, password: str) -> tuple[bool, str]:
    _init_users()
    users = json.loads(USERS_FILE.read_text())
    if username not in users:
        return False, "User not found"
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if users[username]["password"] != hashed:
        return False, "Wrong password"
    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    return True, "Welcome!"


def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.rerun()


def current_user() -> str:
    return st.session_state.get("username", "Guest")
