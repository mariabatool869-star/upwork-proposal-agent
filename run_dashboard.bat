@echo off
cd /d "%~dp0"
echo Upwork AI Agent Dashboard
echo Open http://localhost:8501 in your browser
echo.
python -m streamlit run dashboard/app.py
