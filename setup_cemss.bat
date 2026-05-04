@echo off
title CASS Setup - v11.1
cls
echo ==================================================
echo      CASS - Camera Alert Surveillance System
echo          Setup ^& Installation Script
echo                    v11.1
echo ==================================================
echo.
echo This script will help you set up CASS for the first time.
echo.
echo What this script does:
echo   - Checks Python version
echo   - Installs required dependencies
echo   - Creates configuration files
echo   - Initializes database
echo   - Verifies system readiness
echo.
echo ==================================================
echo.
pause
echo.
python setup.py
pause
