@echo off
echo.
echo ================================================================
echo   SENTINEL HUB v2.0 - COMMAND CENTER
echo ================================================================
echo.
echo [SYSTEM] INITIALIZING DASHBOARD...
echo [SYSTEM] TARGET: http://localhost:8505
echo.
echo Please wait... Browser will open automatically.
echo.
echo ================================================================

echo [SYSTEM] CHECKING PORT 8505...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8505" ^| find "LISTENING"') do (
  echo [SYSTEM] KILLING ZOMBIE PROCESS %%a ON PORT 8505...
  taskkill /f /pid %%a >nul 2>&1
)

cd /d "%~dp0"
streamlit run dashboard.py --server.port 8505 --theme.base "dark"

pause
