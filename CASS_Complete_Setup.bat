@echo off
title CASS Complete Setup & Start
cls
echo ==================================================
echo      CASS - Camera Alert Surveillance System
echo         Complete Initialization & Startup
echo ==================================================
echo.
echo This script will:
echo   1. Check system requirements and dependencies
echo   2. Initialize the database (if needed)
echo   3. Verify Ollama AI status and models
echo   4. Start the CASS Server
echo.
pause
echo.

echo [SETUP] Step 1/2: Running initialization checks...
echo.
python setup.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Setup failed or was cancelled.
    echo Please resolve the issues above before running CASS.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [START] Step 2/2: Starting CASS Server...
echo.
echo Server will be accessible at: http://localhost:5000
echo.
python start.py

echo.
echo CASS Server has stopped.
pause
