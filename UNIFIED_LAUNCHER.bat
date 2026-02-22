@echo off
setlocal
cd /d "%~dp0"
title SENTINEL HUB : UNIFIED DEBUG CONSOLE
color 0b

echo ============================================================
echo      SENTINEL HUB : UNIFIED DEBUG CONSOLE
echo ============================================================
echo [!] This window will stay open to show all errors.
echo.

:: 1. Dependency Check
echo [1/3] Verifying Python Environment...
python -m pip install fastapi uvicorn websockets requests
if %errorlevel% neq 0 (
    echo [ERROR] Failed to verify/install dependencies.
    pause
    exit /b
)

:: 2. Launching Sentinel Brain (API)
echo.
echo [2/3] Launching Sentinel Brain (FastAPI)...
echo [INFO] Close this window to stop the entire system.
echo.

:: We will use a separate window but NOT MINIMIZED so errors are visible
start "SENTINEL_BRAIN_LOGS" cmd /k "python src/api/main_api.py"

echo [SYSTEM] Waiting 5 seconds for Brain initialization...
timeout /t 5 /nobreak > nul

:: 3. Launching Engine
echo.
echo [3/3] Launching Sentinel Bot Engine...
echo.

:: Check if browser should open
echo [SYSTEM] Attempting to open Dashboard: http://localhost:8000
start http://localhost:8000

:: Run the bot in THIS window
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [CRITICAL] Bot Engine crashed.
    echo Please check the error message above.
)

echo.
echo [SYSTEM] Session termniated. Press any key to close all logs.
pause
taskkill /f /fi "windowtitle eq SENTINEL_BRAIN_LOGS" >nul 2>&1
