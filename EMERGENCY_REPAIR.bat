@echo off
setlocal
cd /d %~dp0
title SENTINEL HUB : EMERGENCY REPAIR & START
color 0e

echo ============================================================
echo      SENTINEL HUB : EMERGENCY REPAIR SYSTEM
echo ============================================================
echo.

:: 1. Clear any stuck processes on Port 8000
echo [1/4] Clearing blocked ports (8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak > nul

:: 2. Verify Python Dependencies
echo [2/4] Verifying Core Dependencies...
python -m pip install fastapi uvicorn websockets requests >nul 2>&1

:: 3. Launch the Brain (API)
echo [3/4] Launching Sentinel Brain...
start "SENTINEL_BRAIN" cmd /k "python src/api/main_api.py"

:: Wait for stabilization
echo Waiting for Brain to initialize (7s)...
timeout /t 7 /nobreak > nul

:: 4. Verify Local Connection
echo [4/4] Verifying Local Connection...
powershell -Command "try { $c = iwr -Uri http://localhost:8000 -UseBasicParsing -TimeoutSec 2; echo 'SUCCESS: Brain is Online' } catch { echo 'ERROR: Brain is still unreachable' }"

echo.
echo ------------------------------------------------------------
echo IF SUCCESSFUL: Your dashboard is opening now...
echo IF ERROR: Please check the 'SENTINEL_BRAIN' window for errors.
echo ------------------------------------------------------------
echo.

start http://localhost:8000

:: Start the Bot
echo [!] Starting Bot Engine...
python main.py

pause
