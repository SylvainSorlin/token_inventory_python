"""
Settings dialog — Tenant ID + Client ID only. No secret field.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from config import Config
from . import get_icon_path


class SettingsDialog(tk.Toplevel):
    """Modal dialog for editing the app settings (no client secret)."""

    def __init__(self, parent, config: Config, on_save: Optional[Callable] = None):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save

        self.title("Settings")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Set window icon
        try:
            self.iconbitmap(get_icon_path())
        except Exception:
            pass

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

        # Info
        info = (
            "Entra app registration requirements:\n"
            "  • Redirect URI: http://localhost (Web)\n"
            "  • Allow public client flows: Yes\n"
            "  • Delegated permissions (admin-consented):\n"
            "      Policy.ReadWrite.AuthenticationMethod\n"
            "      UserAuthenticationMethod.ReadWrite.All\n"
            "      User.Read.All · Directory.Read.All\n"
            "  • No client secret needed"
        )
        ttk.Label(self, text=info, foreground="gray", justify="left",
                  font=("", 9)).pack(padx=18, anchor="w", pady=(4, 8))

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
