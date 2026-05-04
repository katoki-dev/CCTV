@echo off
title CASS - Complete Setup and Start
cls

echo ==================================================
echo      CASS - Camera Alert Surveillance System
echo          Complete Setup and Start Script
echo                    v11.1
echo ==================================================
echo.

REM Check if this is first-time setup or regular start
if exist ".env" (
    if exist "database.db" (
        goto :START_SYSTEM
    )
)

:FIRST_TIME_SETUP
echo This appears to be a FIRST-TIME installation.
echo.
echo The setup process will:
echo   1. Check Python version (3.8+ required)
echo   2. Install all dependencies (may take 5-10 minutes)
echo   3. Create configuration file (.env)
echo   4. Initialize database
echo   5. Create required directories
echo.
echo Press any key to begin setup, or Ctrl+C to cancel.
pause >nul
echo.

echo ============================================================
echo   STEP 1: Running CASS Setup
echo ============================================================
echo.
python setup.py
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   Setup failed! Please check errors above.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup completed successfully!
echo ============================================================
echo.
echo IMPORTANT: Please edit the .env file to configure:
echo   - Email settings (for alerts)
echo   - Secret key (for security)
echo   - WhatsApp settings (optional)
echo.
echo Configuration file location: .env
echo.
echo Would you like to:
echo   [1] Edit .env file now (opens notepad)
echo   [2] Start CASS anyway (use defaults)
echo   [3] Exit (configure later)
echo.
choice /c 123 /n /m "Enter your choice (1-3): "

if errorlevel 3 (
    echo.
    echo Setup complete. Run this script again when ready to start.
    pause
    exit /b 0
)

if errorlevel 2 goto :START_SYSTEM

if errorlevel 1 (
    echo.
    echo Opening .env file for editing...
    start /wait notepad .env
    echo.
    echo Configuration file updated.
    echo.
)

:START_SYSTEM
echo.
echo ============================================================
echo   STEP 2: Starting CASS System
echo ============================================================
echo.
echo Server will be accessible at: http://localhost:5000
echo Default Login: admin / admin
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================
echo.

REM Start the CASS system
python start.py

echo.
echo.
echo ============================================================
echo   CASS Server has stopped.
echo ============================================================
pause
