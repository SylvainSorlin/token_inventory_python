""""GUI package with icon resource helper."""
import sys
import os


def get_icon_path():
    """Get the path to favico.ico, works both in dev and PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        return os.path.join(sys._MEIPASS, 'favico.ico')
    else:
        # Running in dev mode
        return 'favico.ico'"