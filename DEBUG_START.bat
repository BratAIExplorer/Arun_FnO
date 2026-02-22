@echo off
:: Simplified Sentinel Hub Startup
:: This version removes all complex checks to ensure it runs on every Windows version
echo ============================================================
echo      SENTINEL HUB : EMERGENCY STARTUP
echo ============================================================
echo.

:: Ensure we are in the right folder
echo [1] Locking onto project directory...
cd /d "%~dp0"
echo     Current Path: %cd%
echo.

:: Start the API Server in its own window
echo [2] Launching Sentinel Brain (API)...
start "SENTINEL_API" cmd /k "python src/api/main_api.py"

:: Wait 3 seconds
echo [3] Waiting for API stabilization...
timeout /t 3

:: Automatically launch the dashboard in browser
echo [4] Opening Dashboard...
start http://localhost:8000

:: Start the Trading Bot
echo [5] Starting Sentinel Bot Engine...
echo.
python main.py

echo.
echo [6] Bot session ended or crashed.
pause
