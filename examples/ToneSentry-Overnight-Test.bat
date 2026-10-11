@echo off
setlocal DisableDelayedExpansion
rem Tone Sentry 0.8.5 passes the completed MP3 filename as argument one.
rem This script only appends a local receipt log. It does not transfer audio.

set "LogFolder=%~dp0logs"
set "LogFile=%LogFolder%\ToneSentry-overnight.log"
if not exist "%LogFolder%\" mkdir "%LogFolder%" 2>nul
if not exist "%LogFolder%\" exit /b 1

if "%~1"=="" goto NoFilename
>>"%LogFile%" echo [%date% %time%] [%COMPUTERNAME%] RECORDING "%~1"
if errorlevel 1 exit /b 1
exit /b 0

:NoFilename
>>"%LogFile%" echo [%date% %time%] [%COMPUTERNAME%] NO_FILENAME - manual launch or non-recording trigger
if errorlevel 1 exit /b 1
exit /b 0
