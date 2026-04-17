"""
Modal dialogs for token operations (assign, activate, CSV import).
All dialogs are standard tkinter Toplevel windows — no external UI lib.
"""
import tkinter as tk
from tkinter import ttk, filedialog
import threading
from typing import Callable
from utils import center_tk_window

from api.graph_api import GraphClient, GraphError
from api.totp import generate_totp_code
from . import get_icon_path


class AssignDialog(tk.Toplevel):
    """Pick a user → assign a token to them."""

    def __init__(self, parent, api: GraphClient, token_id: str,
                 serial: str, on_done: Callable):
        super().__init__(parent)
        self.api, self.token_id, self.serial = api, token_id, serial
        self.on_done = on_done
        self.selected_user = None
        self.users_data = []
        self._search_gen = 0          # generation counter — stale results are discarded
        self._debounce_id = None      # after() id for debounce timer

        self.title(f"Assign token {serial}")
        self.geometry("520x420")
        self.minsize(520, 420)
        self.transient(parent)
        self.grab_set()

        # Set window icon
        try:
            self.iconbitmap(get_icon_path())
        except Exception:
            pass

        # Position relative to parent
        center_tk_window.center_on_parent(parent, self)

        ttk.Label(self, text=f"Assign {serial} to…",
                  font=("", 13, "bold")).pack(pady=(12, 4))

        # Search
        sf = ttk.Frame(self); sf.pack(fill="x", padx=14, pady=4)
        ttk.Label(sf, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        e = ttk.Entry(sf, textvariable=self.search_var, width=40)
        e.pack(side="left", padx=6)
        e.bind("<KeyRelease>", self._on_search)

        # Listbox
        lf = ttk.Frame(self); lf.pack(fill="both", expand=True, padx=14, pady=4)
        self.lb = tk.Listbox(lf, font=("", 10)); self.lb.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(lf, command=self.lb.yview); sb.pack(side="right", fill="y")
        self.lb.config(yscrollcommand=sb.set)
        self.lb.bind("<<ListboxSelect>>", self._on_select)

        # Status + buttons
        self.status = ttk.Label(self, text=""); self.status.pack(pady=4)
        bf = ttk.Frame(self); bf.pack(pady=8)
        self.assign_btn = ttk.Button(bf, text="Assign", command=self._assign, state="disabled")
        self.assign_btn.pack(side="left", padx=4)
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="left", padx=4)

        self._load_users()

    def _on_search(self, _):
        # Debounce: wait 300ms after last keystroke before firing the search
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self._fire_search)

    def _fire_search(self):
        self._debounce_id = None
        q = self.search_var.get().strip()
        if len(q) >= 2 or len(q) == 0:
            self._load_users(q)

    def _load_users(self, query=""):
        self._search_gen += 1
        gen = self._search_gen        # capture current generation
        self.status.config(text="Loading users…")
        self.lb.delete(0, tk.END); self.users_data.clear()
        def work():
            try:
                users = self.api.search_users(query)
                # Only update UI if this is still the latest search
                self.after(0, lambda: self._fill_users(users, gen))
            except GraphError as e:
                self.after(0, lambda: self.status.config(text=f"Error: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _fill_users(self, users, gen):
        # Discard results from an outdated search
        if gen != self._search_gen:
            return
        self.lb.delete(0, tk.END); self.users_data.clear()
        for u in users:
            dn = u.get("displayName", "")
            upn = u.get("userPrincipalName", "")
            self.lb.insert(tk.END, f"{dn}  ({upn})")
            self.users_data.append(u)
        self.status.config(text=f"{len(users)} user(s)")

    def _on_select(self, _):
        sel = self.lb.curselection()
        self.selected_user = self.users_data[sel[0]] if sel else None
        self.assign_btn.config(state="normal" if self.selected_user else "disabled")

    def _assign(self):
        if not self.selected_user:
            return
        uid = self.selected_user["id"]
        self.assign_btn.config(state="disabled")
        self.status.config(text="Assigning…")
        def work():
            try:
                self.api.assign_token(uid, self.token_id)
                self.after(0, lambda: self.status.config(text="Assigned ✓"))
                self.after(800, self._done)
            except GraphError as e:
                self.after(0, lambda: self.status.config(text=f"Error: {e}"))
                self.after(0, lambda: self.assign_btn.config(state="normal"))
        threading.Thread(target=work, daemon=True).start()

    def _done(self):
        self.on_done()
        self.destroy()


class ActivateDialog(tk.Toplevel):
    """Enter (or auto-generate) the OTP code to activate a token."""

    def __init__(self, parent, api: GraphClient, token_id: str,
                 user_id: str, serial: str, user_name: str, on_done: Callable):
        super().__init__(parent)
        self.api = api
        self.token_id, self.user_id = token_id, user_id
        self.serial, self.user_name = serial, user_name
        self.on_done = on_done

        self.title(f"Activate {serial}")
        self.geometry("440x330")
        self.minsize(440, 330)
        self.transient(parent)
        self.grab_set()

        # Set window icon
        try:
            self.iconbitmap(get_icon_path())
        except Exception:
            pass

        # Position relative to parent
        center_tk_window.center_on_parent(parent, self)

        ttk.Label(self, text=f"Activate {serial}",
                  font=("", 13, "bold")).pack(pady=(12, 2))

        ttk.Label(self, text=f"for {user_name}",
                  foreground="gray").pack(pady=(0, 8))

        ff = ttk.LabelFrame(self, text="Verification code"); ff.pack(padx=14, pady=4, fill="x")
        self.code_var = tk.StringVar()
        ttk.Entry(ff, textvariable=self.code_var, width=12,
                  font=("", 14)).pack(pady=8, padx=10)

        sf = ttk.LabelFrame(self, text="Auto-generate from secret"); sf.pack(padx=14, pady=4, fill="x")
        self.secret_var = tk.StringVar()
        e = ttk.Entry(sf, textvariable=self.secret_var, width=44)
        e.pack(pady=8, padx=10)
        e.bind("<KeyRelease>", self._gen)

        self.status = ttk.Label(self, text=""); self.status.pack(pady=4)
        bf = ttk.Frame(self); bf.pack(pady=8)
        self.act_btn = ttk.Button(bf, text="Activate", command=self._activate)
        self.act_btn.pack(side="left", padx=4)
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        
    def _gen(self, _):
        s = self.secret_var.get().strip()
        if s:
            code = generate_totp_code(s)
            if code:
                self.code_var.set(code)
                self.status.config(text="Code generated ✓", foreground="green")
            else:
                self.status.config(text="Invalid secret", foreground="red")

    def _activate(self):
        code = self.code_var.get().strip()
        if not code or len(code) < 6 or not code.isdigit():
            self.status.config(text="Enter a valid 6-digit code", foreground="red")
            return
        self.act_btn.config(state="disabled")
        self.status.config(text="Activating…", foreground="black")
        def work():
            try:
                ok = self.api.activate_token(self.user_id, self.token_id, code)
                if ok:
                    self.after(0, lambda: self.status.config(text="Activated ✓", foreground="green"))
                    self.after(800, self._done)
                else:
                    self.after(0, lambda: self.status.config(text="Activation failed", foreground="red"))
                    self.after(0, lambda: self.act_btn.config(state="normal"))
            except GraphError as e:
                self.after(0, lambda: self.status.config(text=f"Error: {e}", foreground="red"))
                self.after(0, lambda: self.act_btn.config(state="normal"))
        threading.Thread(target=work, daemon=True).start()

    def _done(self):
        self.on_done()
        self.destroy()


class ImportCSVDialog(tk.Toplevel):
    """Paste CSV text → bulk import / assign / activate."""

    def __init__(self, parent, api: GraphClient, on_done: Callable):
        super().__init__(parent)
        self.api, self.on_done = api, on_done

        self.title("Import CSV tokens")
        self.geometry("620x520")
        self.minsize(620, 520)
        self.transient(parent)
        self.grab_set()

        # Set window icon
        try:
            self.iconbitmap(get_icon_path())
        except Exception:
            pass

        # Position relative to parent
        center_tk_window.center_on_parent(parent, self)

        ttk.Label(self, text="Import CSV Tokens",
                  font=("", 14, "bold")).pack(pady=10)

        # Mode selector
        mf = ttk.LabelFrame(self, text="Import mode"); mf.pack(padx=14, pady=4, fill="x")
        self.mode_var = tk.StringVar(value="import_assign_activate")
        self.mode_var.trace_add("write", self._on_mode_change)
        for label, val in [("Import only", "import_only"),
                           ("Import & Assign", "import_assign"),
                           ("Import, Assign & Activate", "import_assign_activate")]:
            ttk.Radiobutton(mf, text=label, variable=self.mode_var, value=val).pack(anchor="w", padx=20, pady=1)
        self.placeholders = {
            "import_only": "serial number,secret key,timeinterval,manufacturer,model\n1100000,JBSWY3DPEHPK3PXP,30,Token2,C203",
            "import_assign": "upn,serial number,secret key,timeinterval,manufacturer,model\nuser@domain.com,1100000,JBSWY3DPEHPK3PXP,30,Token2,C203",
            "import_assign_activate": "upn,serial number,secret key,timeinterval,manufacturer,model\nuser@domain.com,1100000,JBSWY3DPEHPK3PXP,30,Token2,C203"
        }

        # CSV text area
        cf = ttk.LabelFrame(self, text="CSV data"); cf.pack(padx=14, pady=4, fill="both", expand=True)

        # Button frame for CSV file selection
        csv_btn_frame = ttk.Frame(cf)
        csv_btn_frame.pack(fill="x", padx=4, pady=4)
        ttk.Button(csv_btn_frame, text="Load CSV File", command=self._load_csv_file).pack(side="left", padx=4)

        self.csv_text = tk.Text(cf, wrap="none", font=("Consolas", 10), height=10)
        self.csv_text.pack(fill="both", expand=True, padx=4, pady=4)
        self._on_mode_change()

        self.status = ttk.Label(self, text="", wraplength=580)
        self.status.pack(pady=4)

        bf = ttk.Frame(self); bf.pack(pady=8)
        self.imp_btn = ttk.Button(bf, text="Import", command=self._import)
        self.imp_btn.pack(side="left", padx=4)
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        
    def _on_mode_change(self, *args):
        current = self.csv_text.get("1.0", "end-1c").strip()

        # Ne change que si vide ou déjà égal à un placeholder
        if current and current not in self.placeholders.values():
            return

        mode = self.mode_var.get()
        placeholder = self.placeholders.get(mode, "")

        self.csv_text.delete("1.0", "end")
        self.csv_text.insert("1.0", placeholder)

    def _load_csv_file(self):
        """Load CSV data from a file."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select CSV file",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    csv_content = f.read()
                self.csv_text.delete("1.0", "end")
                self.csv_text.insert("1.0", csv_content)
                self.status.config(text=f"File loaded: {file_path}", foreground="green")
            except Exception as e:
                self.status.config(text=f"Error loading file: {e}", foreground="red")

    def _import(self):
        csv_data = self.csv_text.get("1.0", "end-1c").strip()
        if not csv_data:
            self.status.config(text="Paste CSV data first", foreground="red")
            return
        mode = self.mode_var.get()
        self.imp_btn.config(state="disabled")
        self.status.config(text="Importing…", foreground="black")

        def work():
            try:
                results = self.api.import_csv(csv_data, mode)
                ok = sum(1 for r in results.values() if r.get("success"))
                total = len(results)
                color = "green" if ok == total else "orange"
                self.after(0, lambda: self.status.config(
                    text=f"Done: {ok}/{total} succeeded", foreground=color))
                self.after(1500, self._done)
            except Exception as e:
                self.after(0, lambda: self.status.config(text=f"Error: {e}", foreground="red"))
                self.after(0, lambda: self.imp_btn.config(state="normal"))
        threading.Thread(target=work, daemon=True).start()

    def _done(self):
        self.on_done()
        self.destroy()
