@echo off
REM Quick start for Windows — run by double-clicking or from Command Prompt

echo === Installing dependencies ===
pip install -r requirements.txt

echo.
echo === Publishing sample report ===
python publish_report.py --slug prospex-mn360 --data-json templates\report_data.example.json

echo.
echo === Starting web server ===
echo Open in browser: http://localhost:5000/report/prospex-mn360
echo Press Ctrl+C to stop the server
python web_app.py
