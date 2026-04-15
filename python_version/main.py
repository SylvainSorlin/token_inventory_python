"""
TOTP Token Inventory - Main Entry Point
Lightweight Python application for managing Microsoft Entra ID hardware tokens
"""
import sys
from gui.main_window import MainWindow

def main():
    """Main application entry point"""
    try:
        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
