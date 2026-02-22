@echo off
echo Starting F&O Trading Bot Dashboard...
echo.
echo Dashboard will open in your browser automatically
echo Press Ctrl+C to stop
echo.

streamlit run dashboard.py --server.port 8505
