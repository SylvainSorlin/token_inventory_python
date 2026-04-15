@echo off
REM Quick run script - checks if dependencies are installed, then runs app

echo Starting TOTP Token Inventory...
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Virtual environment not found.
    echo Running setup first...
    echo.
    call setup_dev.bat
)

REM Activate venv and run
call venv\Scripts\activate.bat
python main.py

pause
