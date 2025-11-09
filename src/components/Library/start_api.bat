@echo off
echo ============================================================
echo BOTANICAL LIBRARY API SERVER
echo ============================================================
echo.

REM Check if database exists
if not exist "%~dp0botanical_library.db" (
    echo Database not found. Creating database...
    python "%~dp0convert_to_sqlite.py"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create database
        pause
        exit /b 1
    )
    echo.
)

echo Starting API server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python "%~dp0api_server.py"

pause
