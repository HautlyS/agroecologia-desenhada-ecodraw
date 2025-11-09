@echo off
title Botanical Library - Browser Setup
color 0A

echo.
echo ============================================================
echo    BOTANICAL LIBRARY - BROWSER-BASED SETUP
echo    No backend server needed!
echo ============================================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Installing npm dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo     ✓ Dependencies installed

echo.
echo [2/4] Checking for Python (optional, for database building)...
python --version >nul 2>&1
if errorlevel 1 (
    echo     ⚠ Python not found
    echo     You can still use the app if botanical_library.db exists
    echo     Or let GitHub Actions build it automatically
) else (
    echo     ✓ Python found
    
    echo.
    echo [3/4] Building SQLite database...
    if exist "src\components\Library\botanical_library.db" (
        echo     Database already exists
        choice /C YN /M "Rebuild database"
        if errorlevel 2 goto skip_build
    )
    
    python src\components\Library\convert_to_sqlite.py
    if errorlevel 1 (
        echo     ⚠ Database build failed
        echo     The app will try to load existing database
    ) else (
        echo     ✓ Database built successfully
    )
)

:skip_build
echo.
echo [4/4] Checking database...
if exist "src\components\Library\botanical_library.db" (
    echo     ✓ Database found
) else (
    echo     ⚠ Database not found
    echo     The app will show an error until database is created
    echo.
    echo     Options:
    echo     1. Run: python src\components\Library\convert_to_sqlite.py
    echo     2. Push to GitHub and let Actions build it
    echo     3. Download from GitHub releases
)

echo.
echo ============================================================
echo    SETUP COMPLETE!
echo ============================================================
echo.
echo The Botanical Library runs entirely in your browser!
echo No backend server needed.
echo.
echo Next steps:
echo   1. Run: npm run dev
echo   2. Open the Botanical Library
echo   3. Look for "🟢 Carregado" indicator
echo.
echo The database (360 KB) will be loaded into browser memory.
echo All queries run locally - instant results!
echo.
echo ============================================================
echo.
pause
