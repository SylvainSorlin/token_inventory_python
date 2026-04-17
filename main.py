"""
TOTP Token Inventory — MSAL Delegated Edition
Manages hardware OATH tokens in Microsoft Entra ID via interactive sign-in.
No client secret. No application permissions. Full audit trail.
"""
import sys

from gui.main_window import MainWindow


def main():
    try:
        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
