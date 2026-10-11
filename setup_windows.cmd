@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install ".[encoder]"
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m tonepage init
echo Setup complete. Open launch_windows.cmd to use the receiver console.
pause

