@echo off
setlocal
title CASS System Setup and Launcher

echo ========================================================
echo   CASS - Camera Alert Surveillance System
echo   Automated Setup and Startup Script
echo ========================================================
echo.

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)
echo [OK] Python found.

REM Install Requirements
echo.
echo [1/4] Checking and installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [WARNING] Some dependencies failed to install.
        pause
    ) else (
        echo [OK] Dependencies installed.
    )
) else (
    echo [WARNING] requirements.txt not found. Skipping dependency install.
)

REM Check Ollama
echo.
echo [2/4] Checking Ollama service...
timeout /t 2 >nul
tasklist /fi "imagename eq ollama.exe" | find /i "ollama.exe" >nul
if %errorlevel% neq 0 (
    echo [WARNING] Ollama is not running!
    echo Please start the Ollama application for AI features to work.
    echo Attempting to start Ollama logic (if in path)...
    start ollama serve
    timeout /t 5
) else (
    echo [OK] Ollama is running.
)

REM Pull AI Models
echo.
echo [3/4] Pulling required AI models (MiniCPM-V)...
echo This may take a while if not already downloaded.
ollama pull minicpm-v
if %errorlevel% neq 0 (
    echo [ERROR] Failed to pull 'minicpm-v'. Ensure Ollama is running.
) else (
    echo [OK] Model 'minicpm-v' ready.
)

REM Start System
echo.
echo [4/4] Starting CASS Application...
echo.
echo ========================================================
echo   System is starting...
echo   Stop the server by pressing Ctrl+C in this window.
echo ========================================================
python start.py

pause
