"""
Upwork AI Agent — LOCAL Streamlit dashboard (localhost only).

NOT used on Vercel. The live portfolio site is public/index.html + api/jobs/.

Run:  run_dashboard.bat   or   streamlit run dashboard/streamlit_app.py
Data: same Google Sheets as the agent (python run_agent.py) and Vercel refresh.
"""
import subprocess
import sys
from pathlib import Path

# ============================================================
# FIX: Add root directory to path so config can be found
# ============================================================
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config_loader import load_config

config = load_config()

import pandas as pd
import plotly.express as px
import streamlit as st

from auth import check_auth, current_user, login, logout
from data_utils import get_daily_chart, get_jobs_dataframe, get_recent_jobs, get_sheets_status, get_stats

st.set_page_config(
    page_title="Upwork AI Agent | Portfolio",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background: #f8fafc; }
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white; padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem;
    }
    .hero h1 { margin: 0; font-size: 1.8rem; }
    .hero p { opacity: 0.9; margin: 0.5rem 0 0 0; }
    .stat-box {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 1.2rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .stat-num { font-size: 2rem; font-weight: 700; color: #FF6B00; }
    .stat-lbl { color: #64748b; font-size: 0.85rem; }
    .achievement {
        background: white; border-left: 4px solid #FF6B00;
        padding: 1rem 1.2rem; margin: 0.5rem 0; border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)


def login_screen():
    st.markdown("""
    <div class="hero">
        <h1>🚀 Upwork AI Agent</h1>
        <p>Automated job alerts → AI proposals → Gmail drafts</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login"):
            st.subheader("Sign in")
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Login", width="stretch"):
                ok, msg = login(user, pwd)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.caption("Demo login: **demo** / **demo123**")


if not check_auth():
    login_screen()
    st.stop()


@st.cache_data(ttl=15)
def load_data():
    return get_jobs_dataframe()


df = load_data()
stats = get_stats(df)
daily = get_daily_chart(df)
sheets_ok, sheets_message = get_sheets_status()

if not sheets_ok:
    st.warning(f"**Google Sheets not connected** — {sheets_message}")
elif df.empty:
    st.info(f"**Sheets connected** — {sheets_message} Run the agent locally (`python run_agent.py`) to add jobs.")

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"### 👤 {current_user()}")
    st.caption("AI Automation Portfolio")
    page = st.radio(
        "Menu",
        ["Overview", "Proposals", "Analytics", "About"],
        label_visibility="collapsed",
    )
    st.divider()
    st.metric("Jobs tracked", stats["total_jobs"])
    st.metric("Proposals drafted", stats["drafts"])
    if st.button("🔄 Refresh data", width="stretch"):
        load_data.clear()
        st.rerun()
    can_run_agent = (
        config.agent_can_run_locally()
        if hasattr(config, "agent_can_run_locally")
        else config.CREDENTIALS_FILE.exists() and config.TOKEN_FILE.exists()
    )
    if can_run_agent:
        if st.button("▶ Run agent now", width="stretch"):
            with st.spinner("Running run_agent.py..."):
                r = subprocess.run(
                    [sys.executable, "run_agent.py"],
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if r.returncode == 0:
                    st.success("Agent finished!")
                    load_data.clear()
                    st.rerun()
                else:
                    st.error("Agent failed — check logs/agent.log")
                    with st.expander("Error output"):
                        st.code(r.stderr or r.stdout)
    else:
        st.caption("Run the agent locally with `python run_agent.py` (Gmail OAuth required).")
    st.divider()
    if st.button("Logout", width="stretch"):
        logout()

# --- Overview ---
if page == "Overview":
    st.markdown(f"""
    <div class="hero">
        <h1>Upwork Proposal Automation Agent</h1>
        <p>{config.PROFILE.get('title', '')} · {config.PROFILE.get('rate', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{stats["total_jobs"]}</div><div class="stat-lbl">Jobs Processed</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{stats["drafts"]}</div><div class="stat-lbl">Proposals Drafted</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{stats["match_rate"]}%</div><div class="stat-lbl">Match Rate</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{stats["avg_score"]}/10</div><div class="stat-lbl">Avg Score</div></div>', unsafe_allow_html=True)

    st.subheader("Key achievements")
    for item in config.PROFILE.get("experience_highlights", []):
        st.markdown(f'<div class="achievement">{item}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Jobs this week")
        fig = px.bar(daily, x="Day", y="Jobs", color_discrete_sequence=["#FF6B00"])
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch")
    with col2:
        st.subheader("Status breakdown")
        if not df.empty and "Status" in df.columns:
            counts = df["Status"].value_counts()
            fig = px.pie(values=counts.values, names=counts.index, hole=0.4,
                         color_discrete_sequence=["#22c55e", "#f59e0b", "#3b82f6"])
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Run the agent to populate data.")

    st.subheader("Recent jobs")
    if not sheets_ok:
        st.warning("Fix the Google Sheets connection above to load job data.")
    elif df.empty:
        st.info("No job rows in the sheet yet. Run the agent locally with `python run_agent.py`.")
    else:
        show = get_recent_jobs(df, limit=10).copy()
        if "Date" in show.columns:
            date_col = pd.Series(show["Date"])
            show["Date"] = date_col.apply(
                lambda value: "" if pd.isna(value) else str(value)[:19]
            )
        st.dataframe(show, width="stretch", hide_index=True)
        st.caption("Showing newest jobs first. Click **Refresh data** after running the agent.")

# --- Proposals ---
elif page == "Proposals":
    st.title("📝 Proposal drafts")
    if df.empty:
        st.info("No proposals yet.")
    else:
        drafts = df[df["Status"] == config.STATUS_DRAFTED] if "Status" in df.columns else pd.DataFrame()
        st.success(f"{len(drafts)} proposal(s) drafted by the AI agent")
        for idx, row in drafts.iterrows():
            with st.expander(f"{row.get('Title', 'Job')} — {row.get('Budget', '')}"):
                st.write(f"**Score:** {row.get('Score')}/10")
                if row.get("URL"):
                    st.markdown(f"[Open job link]({row['URL']})")
                st.text_area("Proposal text", row.get("Proposal", ""), height=150, key=f"p_{idx}")
                st.caption("Also saved in Gmail → Drafts")

# --- Analytics ---
elif page == "Analytics":
    st.title("📈 Analytics")
    if df.empty:
        st.info("No data yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total jobs", stats["total_jobs"])
        c2.metric("Drafted", stats["drafts"])
        c3.metric("Skipped", stats["skipped"])

        if "Score" in df.columns:
            st.subheader("Score distribution")
            fig = px.histogram(df, x="Score", nbins=10, color_discrete_sequence=["#FF6B00"])
            fig.update_layout(height=300)
            st.plotly_chart(fig, width="stretch")

        if "Status" in df.columns:
            st.subheader("By status")
            for status, count in df["Status"].value_counts().items():
                pct = count / len(df) * 100
                st.write(f"**{status}:** {count} ({pct:.0f}%)")

# --- About ---
else:
    st.title("About this project")
    st.markdown(f"""
    ### What it does
    This **AI agent** automates my Upwork freelance workflow end-to-end:

    1. **Gmail** — reads Vollna job alerts (`info@vollna.com`)
    2. **Parser** — extracts job title, budget, description from HTML emails
    3. **Scorer** — rates jobs 1–10 against my skills profile
    4. **Gemini AI** — writes tailored 55–75 word proposals
    5. **Gmail drafts** — saves proposals ready to review
    6. **Google Sheets** — logs every job (this dashboard)
    7. **Slack** — notifies when a draft is ready

    ### Stack
    Python · Gmail API · Google Gemini · Google Sheets · Slack · Streamlit

    ### Profile
    **{config.MY_NAME}** — {config.PROFILE.get('bio', '')}

    ### Skills
    {', '.join(config.PROFILE.get('skills', [])[:12])}
    """)