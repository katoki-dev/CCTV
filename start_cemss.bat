@echo off
title CASS Surveillance System v11.1
cls
echo ==================================================
echo      CASS - Camera Alert Surveillance System
echo                    v11.1
echo ==================================================
echo.
echo Starting CASS...
echo.
echo Server will be accessible at: http://localhost:5000
echo Default Login: admin / admin
echo.
echo Press Ctrl+C to stop the server.
echo ==================================================
echo.
python start.py
echo.
echo.
echo CASS Server has stopped.
pause

