@echo off
echo ===================================================
echo   Local AI Guest Gateway - Launcher
echo ===================================================
echo.

rem Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/ and check "Add Python to PATH".
    pause
    exit /b
)

rem Create virtual environment if it does not exist
if not exist "env\Scripts\activate.bat" (
    echo [1/3] Creating virtual environment (env)...
    python -m venv env
) else (
    echo [1/3] Virtual environment found.
)

rem Activate virtual environment and install requirements
echo [2/3] Installing/updating requirements...
call env\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some errors occurred during package installation.
)

rem Start applications
echo [3/3] Starting services...
echo.
echo Starting FastAPI Backend in a new window...
start "FastAPI Backend" cmd /k "title FastAPI Backend && call env\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"

echo Starting Streamlit Dashboard...
echo (To close the system, simply close both black terminal windows)
echo.
streamlit run dashboard.py

pause
