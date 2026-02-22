@echo off
title SENTINEL HUB - COMMAND CENTER
color 0b

echo ============================================================
echo      SENTINEL HUB : UNIFIED COMMAND CENTER v1.0
echo ============================================================
echo.

:: Start the API Server in a new window
echo [SYSTEM] Launching Sentinel Brain (API Server)...
start "SENTINEL_API" cmd /k "python src/api/main_api.py"

:: Wait for API to initialize
timeout /t 3 /nobreak > nul

:: Start the Trading Bot
echo [SYSTEM] Connecting Sentinel Bot to Core...
echo.
python main.py

pause
