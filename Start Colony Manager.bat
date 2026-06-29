@echo off
REM ============================================================
REM  Double-click this file to start the Colony Manager.
REM
REM  A black window will open and stay open - that IS the app
REM  running. Your web browser opens automatically a moment later.
REM  To STOP the app, just close the black window.
REM ============================================================

REM Move into the folder this file lives in, whatever it is called.
cd /d "%~dp0"

REM Open the app in your default web browser after a short delay,
REM so the server has a few seconds to start up first.
start "" /min cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000"

REM Start the app. This keeps running until you close the window.
python run.py

REM If the app stops or fails to start, keep the window open so any
REM message can be read instead of vanishing instantly.
echo.
echo The Colony Manager has stopped. You can close this window.
pause >nul
