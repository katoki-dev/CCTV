@echo off
echo ==========================================
echo      CASS SYSTEM DATA RESET UTILITY
echo ==========================================
echo.
echo This script will delete ALL data including:
echo  - Database (Users, Cameras, Logs)
echo  - System Logs
echo  - Cache files
echo  - Recorded videos (if in default folder)
echo.
echo QUANTION: Make sure the CASS server window is CLOSED before continuing.
echo.
pause

echo.
echo 1. Removing Database...
if exist database.db del /F /Q database.db
if exist instance\database.db del /F /Q instance\database.db

echo 2. Clearing Logs...
if exist logs\*.log del /F /Q logs\*.log

echo 3. Clearing Cache...
if exist cache (
    rd /s /q cache
    mkdir cache
    mkdir cache\frames
)

echo 4. Clearing Recordings...
if exist recordings (
    rd /s /q recordings
    mkdir recordings
)

echo.
echo ==========================================
echo           RESET COMPLETE
echo ==========================================
echo.
echo You can now run start_cass.bat to initialize a fresh system.
echo The admin user (admin/admin) will be recreated automatically.
echo.
pause
