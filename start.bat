@echo off
echo ===================================================
echo   Local AI Guest Gateway - Launcher
echo ===================================================
echo.

rem Check for Python
python --version >nul 2>&1
if errorlevel 1 goto nopython

rem Check virtual environment
if exist "env\Scripts\activate.bat" goto hasenv

echo [1/3] Creating virtual environment (env)...
python -m venv env
goto startinstall

:hasenv
echo [1/3] Virtual environment found.

:startinstall
echo [2/3] Installing/updating requirements...
call env\Scripts\activate.bat
pip install -r requirements.txt

echo [3/3] Starting services...
echo.
echo Starting FastAPI Backend in a new window...
start "FastAPI Backend" cmd /k "title FastAPI Backend && call env\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"

echo Starting Streamlit Dashboard...
echo (To close the system, simply close both black terminal windows)
echo.
streamlit run dashboard.py

pause
exit /b

:nopython
echo [ERROR] Python is not installed or not in PATH!
echo Please install Python from https://www.python.org/ and check "Add Python to PATH".
pause
exit /b
