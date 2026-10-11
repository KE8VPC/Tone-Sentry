@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Run setup_windows.cmd first.
  pause
  exit /b 1
)
start "Tone Page Detect" ".venv\Scripts\pythonw.exe" -m tonepage gui

