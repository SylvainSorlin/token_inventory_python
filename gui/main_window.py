"""
Main application window — token inventory table + toolbar.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, Any, Optional

from config import Config
from auth import AuthManager
from api.graph_api import GraphClient, GraphError
from .settings_dialog import SettingsDialog
from .dialogs import AssignDialog, ActivateDialog, ImportCSVDialog
from . import get_icon_path


class MainWindow(tk.Tk):
    """Root window: toolbar + treeview + context menu."""

    def __init__(self):
        super().__init__()
        self.title("TOTP Token Inventory (MSAL)")
        self.geometry("1200x700")
        self.minsize(1000, 300)

        # Set window icon
        try:
            self.iconbitmap(get_icon_path())
        except Exception:
            pass  # Ignore if icon file not found

        self.config_mgr = Config()
        self.auth = AuthManager(self.config_mgr)
        self.api: Optional[GraphClient] = None
        self.tokens = []
        self.filtered_tokens = []
        self._refresh_job = None
        self.filter_vars = {}

        if not self.config_mgr.is_configured():
            self._show_welcome()
        else:
            self._build_ui()
            self._sign_in_and_load()

    # ── welcome screen (first launch) ────────────────────────────────

    def _show_welcome(self):
        self._welcome = ttk.Frame(self)
        self._welcome.pack(fill="both", expand=True)

        ttk.Label(self._welcome, text="TOTP Token Inventory",
                  font=("", 22, "bold")).pack(pady=(80, 10))
        ttk.Label(self._welcome, text="Delegated authentication — no client secret",
                  foreground="gray", font=("", 12)).pack(pady=4)
        ttk.Button(self._welcome, text="Configure app settings",
                   command=self._open_settings_first).pack(pady=24)

    def _open_settings_first(self):
        def after_save():
            if self.config_mgr.is_configured():
                self._welcome.destroy()
                self.auth.reset()
                self._build_ui()
                self._sign_in_and_load()
        SettingsDialog(self, self.config_mgr, after_save)

    # ── main UI ──────────────────────────────────────────────────────

    def _build_ui(self):
        # Toolbar
        tb = ttk.Frame(self); tb.pack(fill="x", padx=8, pady=6)

        ttk.Label(tb, text="🔐 TOTP Token Inventory",
                  font=("", 15, "bold")).pack(side="left", padx=8)

        # Right-side buttons (packed right-to-left)
        ttk.Button(tb, text="Sign out", command=self._sign_out).pack(side="right", padx=3)
        ttk.Button(tb, text="⚙ Settings", command=self._open_settings).pack(side="right", padx=3)
        ttk.Button(tb, text="📥 Import CSV", command=self._open_import).pack(side="right", padx=3)
        ttk.Button(tb, text="🔄 Refresh", command=self._load_tokens).pack(side="right", padx=3)

        # User label
        self.user_label = ttk.Label(tb, text="", foreground="gray")
        self.user_label.pack(side="right", padx=10)

        # Filter bar
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=8, pady=(0, 6))

        ttk.Label(filter_frame, text="🔍 Filters:", font=("", 10, "bold")).pack(side="left", padx=(8, 10))

        # Serial filter
        ttk.Label(filter_frame, text="Serial:").pack(side="left", padx=(0, 2))
        self.filter_vars["serial"] = tk.StringVar()
        self.filter_vars["serial"].trace_add("write", lambda *_: self._apply_filters())
        ttk.Entry(filter_frame, textvariable=self.filter_vars["serial"], width=12).pack(side="left", padx=(0, 10))

        # User filter
        ttk.Label(filter_frame, text="User:").pack(side="left", padx=(0, 2))
        self.filter_vars["user"] = tk.StringVar()
        self.filter_vars["user"].trace_add("write", lambda *_: self._apply_filters())
        ttk.Entry(filter_frame, textvariable=self.filter_vars["user"], width=20).pack(side="left", padx=(0, 10))

        # Status filter
        ttk.Label(filter_frame, text="Status:").pack(side="left", padx=(0, 2))
        self.filter_vars["status"] = tk.StringVar()
        self.filter_vars["status"].trace_add("write", lambda *_: self._apply_filters())
        status_combo = ttk.Combobox(filter_frame, textvariable=self.filter_vars["status"],
                                     values=["", "assigned", "activated", "available"], width=12, state="readonly")
        status_combo.pack(side="left", padx=(0, 10))

        # Clear filters button
        ttk.Button(filter_frame, text="✖ Clear", command=self._clear_filters, width=8).pack(side="left", padx=(5, 0))

        # Status
        self.status = ttk.Label(self, text="Initializing…", anchor="w")
        self.status.pack(fill="x", padx=14, pady=(0, 2))

        # Treeview
        cols = ("Serial", "Device", "Hash", "Time", "User", "Status", "Last seen")
        container = ttk.Frame(self); container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")
        self.tree = ttk.Treeview(container, columns=cols, show="headings",
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        widths = {"Serial": 120, "Device": 160, "Hash": 90, "Time": 55,
                  "User": 220, "Status": 90, "Last seen": 150}
        for c in cols:
            self.tree.heading(c, text=c, command=lambda _c=c: self._sort(_c))
            self.tree.column(c, width=widths.get(c, 100), anchor="center" if c in ("Hash", "Time", "Status") else "w")

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Button-3>", self._ctx_menu)
        self.tree.bind("<Double-1>", self._dbl_click)

    # ── sign-in ──────────────────────────────────────────────────────

    def _sign_in_and_load(self):
        """Acquire a token (silent or interactive) then load the inventory."""
        self.status.config(text="Signing in…")

        def work():
            try:
                self.auth.get_access_token()          # may open a browser
                self.api = GraphClient(self.auth)
                user = self.auth.signed_in_user or ""
                self.after(0, lambda: self.user_label.config(text=f"Signed in as {user}"))
                self.after(0, self._load_tokens)
            except Exception as e:
                self.after(0, lambda: self._error(f"Sign-in failed: {e}"))
                self.after(0, lambda: self.status.config(text="Not signed in"))

        threading.Thread(target=work, daemon=True).start()

    def _sign_out(self):
        if messagebox.askyesno("Sign out", "Sign out and clear cached tokens?"):
            if self._refresh_job:
                self.after_cancel(self._refresh_job)
                self._refresh_job = None
            self.auth.sign_out()
            self.api = None
            self.user_label.config(text="")
            self.status.config(text="Signed out")
            for item in self.tree.get_children():
                self.tree.delete(item)

    # ── token loading ────────────────────────────────────────────────

    def _load_tokens(self):
        if not self.api:
            self._sign_in_and_load()
            return
        self.status.config(text="Loading tokens…")

        def work():
            try:
                self.tokens = self.api.fetch_tokens()
                self.after(0, self._refresh_table)
                self.after(0, lambda: self.status.config(text=f"{len(self.tokens)} token(s)"))
                self.after(0, self._schedule_refresh)
            except GraphError as e:
                self.after(0, lambda: self._error(f"Load failed: {e}"))
                self.after(0, lambda: self.status.config(text="Load failed"))

        threading.Thread(target=work, daemon=True).start()

    def _schedule_refresh(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None
        if self.config_mgr.auto_refresh:
            interval = self.config_mgr.refresh_interval * 1000
            self._refresh_job = self.after(interval, self._load_tokens)

    def _refresh_table(self):
        self.filtered_tokens = self.tokens.copy()
        self._apply_filters()

    def _apply_filters(self):
        """Apply current filters and refresh the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        serial_filter = self.filter_vars.get("serial", tk.StringVar()).get().lower()
        user_filter = self.filter_vars.get("user", tk.StringVar()).get().lower()
        status_filter = self.filter_vars.get("status", tk.StringVar()).get().lower()

        displayed = 0
        for t in self.tokens:
            assigned = t.get("assignedTo") or {}
            user = assigned.get("displayName", "Unassigned") if assigned else "Unassigned"
            serial = t.get("serialNumber", "")
            status = t.get("status", "")

            # Apply filters
            if serial_filter and serial_filter not in serial.lower():
                continue
            if user_filter and user_filter not in user.lower():
                continue
            if status_filter and status_filter != status.lower():
                continue

            vals = (
                serial,
                f"{t.get('manufacturer', '')}/{t.get('model', '')}",
                t.get("hashFunction", ""),
                f"{t.get('timeIntervalInSeconds', 30)}s",
                user,
                status,
                t.get("lastUsedDateTime", "Never"),
            )
            self.tree.insert("", "end", iid=t["id"], values=vals)
            displayed += 1

        # Update status with filter info
        if serial_filter or user_filter or status_filter:
            self.status.config(text=f"{displayed}/{len(self.tokens)} token(s) (filtered)")
        else:
            self.status.config(text=f"{len(self.tokens)} token(s)")

    def _clear_filters(self):
        """Clear all filters."""
        for var in self.filter_vars.values():
            var.set("")

    def _sort(self, col):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        data.sort()
        for i, (_, k) in enumerate(data):
            self.tree.move(k, "", i)

    # ── context menu ─────────────────────────────────────────────────

    def _selected_token(self) -> Optional[Dict[str, Any]]:
        sel = self.tree.selection()
        if not sel:
            return None
        tid = sel[0]
        return next((t for t in self.tokens if t.get("id") == tid), None)

    def _ctx_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        tok = self._selected_token()
        if not tok:
            return
        menu = tk.Menu(self, tearoff=0)
        assigned = tok.get("assignedTo")
        if not assigned:
            menu.add_command(label="Assign to user…", command=self._assign)
            menu.add_separator()
            menu.add_command(label="Delete token", command=self._delete)
        else:
            if tok.get("status") != "activated":
                menu.add_command(label="Activate…", command=self._activate)
            menu.add_command(label="Unassign", command=self._unassign)
        menu.post(event.x_root, event.y_root)

    def _dbl_click(self, _):
        tok = self._selected_token()
        if not tok:
            return
        if not tok.get("assignedTo"):
            self._assign()
        elif tok.get("status") != "activated":
            self._activate()

    # ── actions ──────────────────────────────────────────────────────

    def _assign(self):
        tok = self._selected_token()
        if tok and self.api:
            AssignDialog(self, self.api, tok["id"], tok.get("serialNumber", ""), self._load_tokens)

    def _activate(self):
        tok = self._selected_token()
        if not tok or not self.api:
            return
        assigned = tok.get("assignedTo") or {}
        if not assigned:
            self._error("Token must be assigned first")
            return
        ActivateDialog(self, self.api, tok["id"], assigned["id"],
                       tok.get("serialNumber", ""), assigned.get("displayName", ""),
                       self._load_tokens)

    def _unassign(self):
        tok = self._selected_token()
        if not tok or not self.api:
            return
        assigned = tok.get("assignedTo") or {}
        if not assigned:
            return
        if not messagebox.askyesno("Confirm", "Unassign this token?"):
            return
        self.status.config(text="Unassigning…")
        def work():
            try:
                self.api.unassign_token(assigned["id"], tok["id"])
                self.after(0, self._load_tokens)
            except GraphError as e:
                self.after(0, lambda: self._error(f"Unassign failed: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _delete(self):
        tok = self._selected_token()
        if not tok or not self.api:
            return
        if not messagebox.askyesno("Confirm", "Delete this token permanently?"):
            return
        self.status.config(text="Deleting…")
        def work():
            try:
                self.api.delete_token(tok["id"])
                self.after(0, self._load_tokens)
            except GraphError as e:
                self.after(0, lambda: self._error(f"Delete failed: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _open_import(self):
        if self.api:
            ImportCSVDialog(self, self.api, self._load_tokens)

    def _open_settings(self):
        def after():
            self.auth.reset()
            self._schedule_refresh()
            self._sign_in_and_load()
        SettingsDialog(self, self.config_mgr, after)

    # ── util ─────────────────────────────────────────────────────────

    def _error(self, msg):
        messagebox.showerror("Error", msg)
