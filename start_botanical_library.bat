@echo off
title Botanical Library - Complete Setup
color 0A

echo.
echo ============================================================
echo    BOTANICAL LIBRARY - COMPLETE SETUP
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Checking Python dependencies...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo Installing Flask and flask-cors...
    pip install Flask flask-cors
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo     ✓ Dependencies OK

echo.
echo [2/5] Checking database...
if not exist "src\components\Library\botanical_library.db" (
    echo Database not found. Creating database...
    python src\components\Library\convert_to_sqlite.py
    if errorlevel 1 (
        echo [ERROR] Failed to create database
        pause
        exit /b 1
    )
) else (
    echo     ✓ Database exists
)

echo.
echo [3/5] Testing API server...
python src\components\Library\test_api.py >nul 2>&1
if errorlevel 1 (
    echo     ⚠ API server not running (will start in next step)
) else (
    echo     ✓ API server already running
)

echo.
echo [4/5] Starting API server...
echo.
echo ============================================================
echo    API SERVER STARTING
echo ============================================================
echo.
echo The API server will start in a new window.
echo Keep that window open while using the Botanical Library.
echo.
echo Server URL: http://localhost:5000
echo.
echo Press any key to start the API server...
pause >nul

start "Botanical Library API Server" cmd /k "python src\components\Library\api_server.py"

echo.
echo Waiting for API server to start...
timeout /t 3 /nobreak >nul

echo.
echo [5/5] Testing API connection...
timeout /t 2 /nobreak >nul

curl -s http://localhost:5000/api/health >nul 2>&1
if errorlevel 1 (
    echo     ⚠ API server may still be starting...
    echo     Check the API server window for any errors.
) else (
    echo     ✓ API server is running!
)

echo.
echo ============================================================
echo    SETUP COMPLETE!
echo ============================================================
echo.
echo Next steps:
echo   1. Start your Vue app: npm run dev
echo   2. Open the Botanical Library in your app
echo   3. Look for the "🟢 Online" indicator
echo.
echo The API server is running in a separate window.
echo Do NOT close that window while using the library!
echo.
echo To stop the API server:
echo   - Close the API server window, or
echo   - Press Ctrl+C in the API server window
echo.
echo ============================================================
echo.
pause
