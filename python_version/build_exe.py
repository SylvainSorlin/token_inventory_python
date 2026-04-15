"""
Build script for creating standalone executable
Uses PyInstaller to create a single .exe file
"""
import PyInstaller.__main__
import sys
import os

def build_exe():
    """Build standalone executable"""

    app_name = "TokenInventory"

    # PyInstaller arguments
    args = [
        'main.py',                          # Main script
        '--name=' + app_name,               # Exe name
        '--onefile',                        # Single exe file
        '--windowed',                       # No console window
        '--clean',                          # Clean cache
        '--noconfirm',                      # Overwrite without asking

        # Add hidden imports
        '--hidden-import=customtkinter',
        '--hidden-import=requests',
        '--hidden-import=PIL',

        # Add data files if needed
        # '--add-data=assets;assets',

        # Icon (if you have one)
        # '--icon=icon.ico',
    ]

    print("Building standalone executable...")
    print(f"Application: {app_name}")
    print("=" * 50)

    PyInstaller.__main__.run(args)

    print("\n" + "=" * 50)
    print("Build complete!")
    print(f"Executable: dist/{app_name}.exe")
    print("=" * 50)

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller not installed")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

    build_exe()
