#Source : https://github.com/jarikmarwede/center-tk-window/tree/master
import tkinter
from typing import Union


def center_on_screen(window: Union[tkinter.Tk, tkinter.Toplevel]):
    """Center a window on the screen."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x_coordinate = int(window.winfo_screenwidth() / 2 - width / 2)
    y_coordinate = int(window.winfo_screenheight() / 2 - height / 2)

    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")


def center_on_parent(root: tkinter.Tk, window: tkinter.Toplevel):
    """Center a window on its parent."""
    window.update_idletasks()
    height = window.winfo_height()
    width = window.winfo_width()
    parent = root.nametowidget(window.winfo_parent())
    x_coordinate = int(parent.winfo_x() + (parent.winfo_width() / 2 - width / 2))
    y_coordinate = int(parent.winfo_y() + (parent.winfo_height() / 2 - height / 2))

    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")


def center(root: tkinter.Tk, window: Union[tkinter.Tk, tkinter.Toplevel]):
    """Center a window on its parent or the screen if there is no parent."""
    if window.winfo_parent():
        center_on_parent(root, window)
    else:
        center_on_screen(window)