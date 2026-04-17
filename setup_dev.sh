#!/bin/bash
# Development setup script for Linux/Mac

echo "========================================"
echo "TOTP Token Inventory - Development Setup"
echo "========================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from your package manager"
    exit 1
fi

echo "[1/4] Creating virtual environment..."
python3 -m venv venv

echo "[2/4] Activating virtual environment..."
source venv/bin/activate

echo "[3/4] Upgrading pip..."
pip install --upgrade pip

echo "[4/4] Installing dependencies..."
pip install -r requirements.txt

echo
echo "========================================"
echo "Setup complete!"
echo "========================================"
echo
echo "To run the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python3 main.py"
echo
echo "To build executable:"
echo "  1. pip install pyinstaller"
echo "  2. python3 build_exe.py"
echo
