"""
Settings dialog — Tenant ID + Client ID only. No secret field.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from utils import center_tk_window
import webbrowser

from config import Config
from . import get_icon_path


class SettingsDialog(tk.Toplevel):
    """Modal dialog for editing the app settings (no client secret)."""

    def __init__(self, parent, config: Config, on_save: Optional[Callable] = None):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save

        self.title("Settings")
        self.geometry("500x390")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Set window icon
        try:
            self.iconbitmap(get_icon_path())
        except Exception:
            pass
        
        # Position relative to parent
        center_tk_window.center_on_parent(parent, self)

        # Form
        ttk.Label(self, text="Microsoft Entra App Settings",
                  font=("", 14, "bold")).pack(pady=(16, 8))

        ff = ttk.LabelFrame(self, text="App registration"); ff.pack(padx=16, pady=6, fill="x")

        ttk.Label(ff, text="Tenant ID:").pack(anchor="w", padx=10, pady=(8, 0))
        self.tenant_var = tk.StringVar(value=config.tenant_id or "")
        ttk.Entry(ff, textvariable=self.tenant_var, width=52).pack(padx=10, pady=(0, 6))

        ttk.Label(ff, text="Client ID:").pack(anchor="w", padx=10)
        self.client_var = tk.StringVar(value=config.client_id or "")
        ttk.Entry(ff, textvariable=self.client_var, width=52).pack(padx=10, pady=(0, 6))

        self.logs_var = tk.BooleanVar(value=config.show_logs)
        ttk.Checkbutton(ff, text="Show operation logs", variable=self.logs_var).pack(anchor="w", padx=10, pady=(4, 10))

        # Auto-refresh settings
        rf = ttk.LabelFrame(self, text="Auto-refresh"); rf.pack(padx=16, pady=6, fill="x")

        self.refresh_var = tk.BooleanVar(value=config.auto_refresh)
        ttk.Checkbutton(rf, text="Enable auto-refresh", variable=self.refresh_var).pack(anchor="w", padx=10, pady=(8, 4))

        interval_frame = ttk.Frame(rf); interval_frame.pack(anchor="w", padx=10, pady=(0, 10))
        ttk.Label(interval_frame, text="Refresh interval:").pack(side="left", padx=(0, 5))
        self.interval_var = tk.StringVar(value=str(config.refresh_interval))
        interval_combo = ttk.Combobox(interval_frame, textvariable=self.interval_var, width=12, state="readonly")
        interval_combo["values"] = ("10", "20", "30", "60", "600")
        interval_combo.pack(side="left")
        ttk.Label(interval_frame, text="seconds").pack(side="left", padx=(5, 0))

        # Github
        github_url = "https://github.com/SylvainSorlin/token_inventory_python"
        url_label = ttk.Label(self, text=github_url, foreground="blue", justify="left", cursor="hand2",
                  font=("", 9))
        url_label.pack(padx=18, anchor="w", pady=(4, 8))
        url_label.bind("<Button-1>", lambda e: webbrowser.open_new(github_url))
        
        # Buttons
        bf = ttk.Frame(self); bf.pack(pady=8)
        ttk.Button(bf, text="Save", command=self._save).pack(side="left", padx=4)
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(bf, text="Clear all", command=self._clear).pack(side="left", padx=4)

    def _save(self):
        t = self.tenant_var.get().strip()
        c = self.client_var.get().strip()
        if not t or not c:
            messagebox.showwarning("Missing fields", "Tenant ID and Client ID are required.", parent=self)
            return
        self.config.tenant_id = t
        self.config.client_id = c
        self.config.show_logs = self.logs_var.get()
        self.config.auto_refresh = self.refresh_var.get()
        try:
            self.config.refresh_interval = int(self.interval_var.get())
        except ValueError:
            pass
        if self.on_save:
            self.on_save()
        self.destroy()

    def _clear(self):
        if messagebox.askyesno("Confirm", "Clear all settings and cached tokens?", parent=self):
            self.config.clear()
            if self.config.cache_path.exists():
                self.config.cache_path.unlink()
            self.tenant_var.set("")
            self.client_var.set("")
            if self.on_save:
                self.on_save()
