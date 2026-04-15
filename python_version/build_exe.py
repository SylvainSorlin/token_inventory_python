"""
Build a standalone .exe with PyInstaller.
Run: python build_exe.py
"""
import subprocess
import sys

def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "TokenInventory",
        "--add-data", "api;api",
        "--add-data", "gui;gui",
        "--add-data", "config.py;.",
        "--add-data", "auth.py;.",
        "--hidden-import", "msal",
        "--hidden-import", "requests",
        "main.py",
    ]
    subprocess.run(cmd, check=True)
    print("\nBuild complete → dist/TokenInventory.exe")

if __name__ == "__main__":
    build()
