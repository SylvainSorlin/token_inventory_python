#!/bin/bash
# Quick run script - checks if dependencies are installed, then runs app

echo "Starting TOTP Token Inventory..."
echo

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found."
    echo "Running setup first..."
    echo
    ./setup_dev.sh
fi

# Activate venv and run
source venv/bin/activate
python main.py
