@echo off
REM ============================================================
REM  Double-click this ONE TIME after downloading, to install
REM  the things Colony Manager needs to run. After this, you only
REM  ever use "Start Colony Manager.bat".
REM ============================================================

cd /d "%~dp0"

echo Installing Colony Manager's requirements. This is a one-time setup
echo and needs an internet connection. Please wait...
echo.

python -m pip install -r requirements.txt

echo.
echo ============================================================
echo  Done! From now on, just double-click:
echo     Start Colony Manager.bat
echo ============================================================
echo.
pause
