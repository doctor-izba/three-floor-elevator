@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -File "%~dp0START_DEMO.ps1"
if errorlevel 1 (
    echo.
    echo Startup failed. See the message above.
)
echo.
pause
