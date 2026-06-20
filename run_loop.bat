@echo off
cd /d "%~dp0"
echo Upwork Proposal Automation - Background Mode
echo Checking Gmail every 30 minutes. Press Ctrl+C to stop.
echo.
python main.py --loop
