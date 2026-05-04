@echo off
REM CASS Installation Script for Windows
REM Quick setup for first-time users

echo ============================================
echo  CASS - Automated Installation Script
echo ============================================
echo.

REM Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)
echo ✓ Python detected

REM Check Ollama
echo.
echo [2/6] Checking Ollama installation...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama not found
    echo Please install from: https://ollama.ai
    echo Press any key to continue without AI features, or Ctrl+C to abort...
    pause >nul
) else (
    echo ✓ Ollama detected
)

REM Install Python dependencies
echo.
echo [3/6] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

REM Pull AI models
echo.
echo [4/6] Downloading AI models (this may take a few minutes)...
ollama pull qwen2.5:0.5b
ollama pull moondream
echo ✓ AI models downloaded

REM Setup environment
echo.
echo [5/6] Creating configuration file...
if not exist .env (
    copy .env.example .env
    echo ✓ .env created from template
) else (
    echo ✓ .env already exists
)

REM Initialize database
echo.
echo [6/6] Initializing database...
python init_db.py
if errorlevel 1 (
    echo ERROR: Database initialization failed
    pause
    exit /b 1
)
echo ✓ Database initialized

echo.
echo ============================================
echo  Installation Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Start Ollama: ollama serve (in a separate window)
echo 2. Start CASS: python app.py
echo 3. Open browser: http://localhost:5000
echo 4. Login: admin / admin
echo.
echo For detailed documentation, see QUICK_START.md
echo.
pause
