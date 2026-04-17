@echo off
REM Token Inventory MSAL — Windows launcher
REM Requires Python 3.10+ in PATH

cd /d "%~dp0"

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

python main.py
