@echo off
cd /d "%~dp0"
echo Upwork Proposal Automation - Single Run
echo.
echo Agent runs locally. Results go to Google Sheets.
echo After it finishes, refresh your Vercel dashboard to see new jobs.
echo.
python main.py
echo.
pause
