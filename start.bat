@echo off
chcp 65001 >nul
echo ===================================================
echo   Local AI Guest Gateway - 一鍵啟動腳本
echo ===================================================
echo.

:: 檢查是否有 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 系統找不到 Python！
    echo 請前往 https://www.python.org/ 安裝，並記得勾選 "Add Python to PATH"。
    pause
    exit /b
)

:: 建立虛擬環境
if not exist "env\Scripts\activate.bat" (
    echo [1/3] 第一次執行，正在建立虛擬環境 (env)...
    python -m venv env
) else (
    echo [1/3] 找到虛擬環境。
)

:: 啟動虛擬環境並安裝相依套件
echo [2/3] 正在安裝或更新相依套件...
call env\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 安裝套件時發生部分錯誤，但將繼續嘗試啟動。
)

:: 啟動應用程式
echo [3/3] 正在啟動服務...
echo.
echo 正在開啟另一個視窗以執行 FastAPI 後端伺服器...
start "FastAPI Backend" cmd /k "title FastAPI Backend && call env\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"

echo 正在啟動 Streamlit 儀表板...
echo (如果您想關閉系統，請直接關閉這兩個黑色的終端機視窗即可)
echo.
streamlit run dashboard.py

pause
