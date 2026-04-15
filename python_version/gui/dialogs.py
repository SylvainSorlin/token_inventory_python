"""
Dialogs for token operations
Assign, Activate, Import dialogs
"""
import customtkinter as ctk
import tkinter as tk
from typing import Callable, List, Dict, Any, Optional
from api.graph_api import GraphAPIClient, GraphAPIError
from api.totp import generate_totp_code

class AssignDialog(ctk.CTkToplevel):
    """Dialog for assigning token to user"""

    def __init__(self, parent, api_client: GraphAPIClient, token_id: str, serial_number: str, on_success: Callable):
        super().__init__(parent)

        self.api_client = api_client
        self.token_id = token_id
        self.serial_number = serial_number
        self.on_success = on_success
        self.selected_user = None

        self.title(f"Assign Token: {serial_number}")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets"""

        # Title
        title = ctk.CTkLabel(
            self,
            text=f"Assign Token: {self.serial_number}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=20)

        # Search frame
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(search_frame, text="Search User:").pack(pady=5, anchor="w", padx=10)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type name or email...")
        self.search_entry.pack(pady=5, padx=10, fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Results listbox
        results_frame = ctk.CTkFrame(self)
        results_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.results_listbox = tk.Listbox(
            results_frame,
            height=10,
            font=("Arial", 11),
            selectmode=tk.SINGLE
        )
        self.results_listbox.pack(side="left", fill="both", expand=True)
        self.results_listbox.bind("<<ListboxSelect>>", self._on_select)

        scrollbar = ctk.CTkScrollbar(results_frame, command=self.results_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.results_listbox.configure(yscrollcommand=scrollbar.set)

        # Store user data
        self.users_data = []

        # Status label
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=5)

        self.assign_btn = ctk.CTkButton(
            button_frame,
            text="Assign",
            command=self._assign_token,
            state="disabled"
        )
        self.assign_btn.pack(side="right", padx=5)

        # Load initial users
        self._load_users()

    def _on_search(self, event):
        """Handle search input"""
        query = self.search_entry.get().strip()
        if len(query) >= 2:
            self._load_users(query)
        elif len(query) == 0:
            self._load_users()

    def _load_users(self, query: str = ""):
        """Load users from API"""
        self.status_label.configure(text="Loading users...")
        self.results_listbox.delete(0, tk.END)
        self.users_data = []

        try:
            users = self.api_client.search_users(query)

            if users:
                for user in users:
                    display_name = user.get('displayName', '')
                    upn = user.get('userPrincipalName', '')
                    self.results_listbox.insert(tk.END, f"{display_name} ({upn})")
                    self.users_data.append(user)

                self.status_label.configure(text=f"Found {len(users)} users")
            else:
                self.status_label.configure(text="No users found")

        except GraphAPIError as e:
            self.status_label.configure(text=f"Error: {e.message}", text_color="red")

    def _on_select(self, event):
        """Handle user selection"""
        selection = self.results_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_user = self.users_data[index]
            self.assign_btn.configure(state="normal")
        else:
            self.selected_user = None
            self.assign_btn.configure(state="disabled")

    def _assign_token(self):
        """Assign token to selected user"""
        if not self.selected_user:
            return

        user_id = self.selected_user.get('id')
        if not user_id:
            return

        self.status_label.configure(text="Assigning token...", text_color="blue")
        self.assign_btn.configure(state="disabled")

        try:
            self.api_client.assign_token(user_id, self.token_id)
            self.status_label.configure(text="Token assigned successfully!", text_color="green")

            # Close after brief delay
            self.after(1000, self._on_complete)

        except GraphAPIError as e:
            self.status_label.configure(text=f"Error: {e.message}", text_color="red")
            self.assign_btn.configure(state="normal")

    def _on_complete(self):
        """Handle completion"""
        if self.on_success:
            self.on_success()
        self.destroy()


class ActivateDialog(ctk.CTkToplevel):
    """Dialog for activating token"""

    def __init__(self, parent, api_client: GraphAPIClient, token_id: str, user_id: str,
                 serial_number: str, user_name: str, on_success: Callable):
        super().__init__(parent)

        self.api_client = api_client
        self.token_id = token_id
        self.user_id = user_id
        self.serial_number = serial_number
        self.user_name = user_name
        self.on_success = on_success

        self.title(f"Activate Token: {serial_number}")
        self.geometry("450x350")
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets"""

        # Title
        title = ctk.CTkLabel(
            self,
            text=f"Activate Token: {self.serial_number}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=20)

        subtitle = ctk.CTkLabel(
            self,
            text=f"for user: {self.user_name}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle.pack(pady=5)

        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Verification code
        ctk.CTkLabel(form_frame, text="Verification Code:").pack(pady=(10, 0), padx=10, anchor="w")
        self.code_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter 6-digit code",
            width=200
        )
        self.code_entry.pack(pady=5, padx=10)

        # Separator
        separator = ctk.CTkLabel(form_frame, text="- OR -", text_color="gray")
        separator.pack(pady=10)

        # Secret key for auto-generation
        ctk.CTkLabel(form_frame, text="Secret Key (auto-generate):").pack(pady=(5, 0), padx=10, anchor="w")
        self.secret_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter secret key"
        )
        self.secret_entry.pack(pady=5, padx=10, fill="x")
        self.secret_entry.bind("<KeyRelease>", self._on_secret_change)

        # Status label
        self.status_label = ctk.CTkLabel(form_frame, text="", text_color="gray")
        self.status_label.pack(pady=10)

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=5)

        self.activate_btn = ctk.CTkButton(
            button_frame,
            text="Activate",
            command=self._activate_token
        )
        self.activate_btn.pack(side="right", padx=5)

    def _on_secret_change(self, event):
        """Handle secret key input"""
        secret = self.secret_entry.get().strip()
        if secret:
            code = generate_totp_code(secret)
            if code:
                self.code_entry.delete(0, 'end')
                self.code_entry.insert(0, code)
                self.status_label.configure(text="Code generated", text_color="green")
            else:
                self.status_label.configure(text="Invalid secret key", text_color="red")

    def _activate_token(self):
        """Activate token"""
        code = self.code_entry.get().strip()

        if not code or len(code) != 6 or not code.isdigit():
            self.status_label.configure(text="Please enter valid 6-digit code", text_color="red")
            return

        self.status_label.configure(text="Activating token...", text_color="blue")
        self.activate_btn.configure(state="disabled")

        try:
            success = self.api_client.activate_token(self.user_id, self.token_id, code)

            if success:
                self.status_label.configure(text="Token activated successfully!", text_color="green")
                self.after(1000, self._on_complete)
            else:
                self.status_label.configure(text="Activation failed", text_color="red")
                self.activate_btn.configure(state="normal")

        except GraphAPIError as e:
            self.status_label.configure(text=f"Error: {e.message}", text_color="red")
            self.activate_btn.configure(state="normal")

    def _on_complete(self):
        """Handle completion"""
        if self.on_success:
            self.on_success()
        self.destroy()


class ImportCSVDialog(ctk.CTkToplevel):
    """Dialog for importing CSV tokens"""

    def __init__(self, parent, api_client: GraphAPIClient, on_success: Callable):
        super().__init__(parent)

        self.api_client = api_client
        self.on_success = on_success

        self.title("Import CSV Tokens")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets"""

        # Title
        title = ctk.CTkLabel(
            self,
            text="Import CSV Tokens",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=20)

        # Import mode
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(mode_frame, text="Import Mode:", font=ctk.CTkFont(weight="bold")).pack(pady=5, anchor="w", padx=10)

        self.mode_var = tk.StringVar(value="import_assign_activate")

        modes = [
            ("Import Only", "import_only"),
            ("Import & Assign", "import_assign"),
            ("Import, Assign & Activate", "import_assign_activate")
        ]

        for text, value in modes:
            ctk.CTkRadioButton(
                mode_frame,
                text=text,
                variable=self.mode_var,
                value=value
            ).pack(pady=2, anchor="w", padx=20)

        # CSV data
        csv_frame = ctk.CTkFrame(self)
        csv_frame.pack(padx=20, pady=10, fill="both", expand=True)

        ctk.CTkLabel(csv_frame, text="CSV Data:", font=ctk.CTkFont(weight="bold")).pack(pady=5, anchor="w", padx=10)

        self.csv_text = ctk.CTkTextbox(csv_frame, height=200)
        self.csv_text.pack(pady=5, padx=10, fill="both", expand=True)

        placeholder = "upn,serial number,secret key,timeinterval,manufacturer,model\nuser@domain.com,1100000,JBSWY3DPEHPK3PXP,30,Token2,miniOTP-1"
        self.csv_text.insert("1.0", placeholder)

        # Status label
        self.status_label = ctk.CTkLabel(self, text="", wraplength=550)
        self.status_label.pack(pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=5)

        self.import_btn = ctk.CTkButton(
            button_frame,
            text="Import",
            command=self._import_csv
        )
        self.import_btn.pack(side="right", padx=5)

    def _import_csv(self):
        """Import CSV data"""
        csv_data = self.csv_text.get("1.0", "end-1c").strip()

        if not csv_data:
            self.status_label.configure(text="Please enter CSV data", text_color="red")
            return

        mode = self.mode_var.get()
        self.status_label.configure(text="Importing tokens...", text_color="blue")
        self.import_btn.configure(state="disabled")

        try:
            results = self.api_client.import_csv_tokens(csv_data, mode)

            success_count = sum(1 for r in results.values() if r.get('success'))
            total_count = len(results)

            self.status_label.configure(
                text=f"Import complete: {success_count}/{total_count} successful",
                text_color="green" if success_count == total_count else "orange"
            )

            self.after(2000, self._on_complete)

        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", text_color="red")
            self.import_btn.configure(state="normal")

    def _on_complete(self):
        """Handle completion"""
        if self.on_success:
            self.on_success()
        self.destroy()
