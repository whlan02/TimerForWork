@echo off
chcp 65001 >nul
echo Starting TimerForWork...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not detected. Please install Python first.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Check and install dependencies
echo Checking dependencies...
pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo Dependencies missing. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    pip show openpyxl >nul 2>&1
    if errorlevel 1 (
        echo Dependencies missing. Installing...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ERROR: Failed to install dependencies.
            pause
            exit /b 1
        )
    ) else (
        echo All dependencies are ready.
    )
)

REM Run the application
echo Starting application...
python -m app.main

REM Pause if there was an error so user can read messages
if errorlevel 1 (
    echo.
    echo Application encountered an error. Please check the messages above.
    pause
)
