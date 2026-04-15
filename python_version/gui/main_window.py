"""
Main Window
Main application window with token table and operations
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any
import threading

from config import Config
from api.graph_api import GraphAPIClient, GraphAPIError
from .settings_window import SettingsWindow
from .dialogs import AssignDialog, ActivateDialog, ImportCSVDialog


class MainWindow(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.title("TOTP Token Inventory")
        self.geometry("1200x700")

        # Configuration
        self.config = Config()
        self.api_client = None
        self.tokens = []

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Check if credentials exist
        if not self.config.has_credentials():
            self._show_initial_settings()
        else:
            self._create_widgets()
            self._load_tokens()

    def _show_initial_settings(self):
        """Show settings on first launch"""
        # Create simple frame with message
        welcome_frame = ctk.CTkFrame(self)
        welcome_frame.pack(fill="both", expand=True, padx=50, pady=50)

        ctk.CTkLabel(
            welcome_frame,
            text="Welcome to TOTP Token Inventory",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=30)

        ctk.CTkLabel(
            welcome_frame,
            text="Please configure your Microsoft Graph credentials to get started.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(pady=10)

        ctk.CTkButton(
            welcome_frame,
            text="Open Settings",
            command=self._open_settings_and_init,
            height=40,
            font=ctk.CTkFont(size=14)
        ).pack(pady=20)

    def _open_settings_and_init(self):
        """Open settings and initialize main window after"""
        def on_save():
            # Destroy welcome frame
            for widget in self.winfo_children():
                widget.destroy()

            # Create main interface
            if self.config.has_credentials():
                self._create_widgets()
                self._load_tokens()

        SettingsWindow(self, self.config, on_save)

    def _create_widgets(self):
        """Create main window widgets"""

        # Top bar
        top_bar = ctk.CTkFrame(self, height=60)
        top_bar.pack(fill="x", padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            top_bar,
            text="🔐 TOTP Token Inventory",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=20)

        # Buttons frame
        buttons_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        buttons_frame.pack(side="right", padx=10)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Refresh",
            command=self._load_tokens,
            width=100
        )
        refresh_btn.pack(side="left", padx=5)

        # Import CSV button
        import_btn = ctk.CTkButton(
            buttons_frame,
            text="📥 Import CSV",
            command=self._open_import_dialog,
            width=120,
            fg_color="#2196F3"
        )
        import_btn.pack(side="left", padx=5)

        # Settings button
        settings_btn = ctk.CTkButton(
            buttons_frame,
            text="⚙️ Settings",
            command=lambda: SettingsWindow(self, self.config, self._on_settings_saved),
            width=100,
            fg_color="gray"
        )
        settings_btn.pack(side="left", padx=5)

        # Clear session button
        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="🚪 Logout",
            command=self._clear_session,
            width=100,
            fg_color="red",
            hover_color="darkred"
        )
        clear_btn.pack(side="left", padx=5)

        # Status bar
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 5))

        # Table frame
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Create Treeview with scrollbars
        tree_container = ctk.CTkFrame(table_frame)
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical")
        hsb = ttk.Scrollbar(tree_container, orient="horizontal")

        # Treeview
        columns = ("Serial", "Device", "Hash", "Time", "User", "Status", "Last Seen")
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="tree headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Configure columns
        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("Serial", width=120, anchor="w")
        self.tree.column("Device", width=150, anchor="w")
        self.tree.column("Hash", width=100, anchor="center")
        self.tree.column("Time", width=60, anchor="center")
        self.tree.column("User", width=200, anchor="w")
        self.tree.column("Status", width=100, anchor="center")
        self.tree.column("Last Seen", width=150, anchor="center")

        # Headings
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))

        # Style
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0,
            font=('Arial', 10)
        )
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Context menu
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", self._on_double_click)

    def _sort_column(self, col):
        """Sort treeview by column"""
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        items.sort()

        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)

    def _on_settings_saved(self):
        """Handle settings save"""
        self._load_tokens()

    def _load_tokens(self):
        """Load tokens from API"""
        if not self.config.has_credentials():
            self._show_error("Please configure credentials in Settings")
            return

        self.status_label.configure(text="Loading tokens...", text_color="blue")

        # Run in thread to avoid blocking UI
        def load():
            try:
                # Create API client
                self.api_client = GraphAPIClient(
                    self.config.tenant_id,
                    self.config.client_id,
                    self.config.client_secret
                )

                # Fetch tokens
                self.tokens = self.api_client.fetch_tokens()

                # Update UI in main thread
                self.after(0, self._update_table)
                self.after(0, lambda: self.status_label.configure(
                    text=f"Loaded {len(self.tokens)} tokens",
                    text_color="green"
                ))

            except GraphAPIError as e:
                self.after(0, lambda: self._show_error(f"API Error: {e.message}"))
                self.after(0, lambda: self.status_label.configure(
                    text="Failed to load tokens",
                    text_color="red"
                ))

        threading.Thread(target=load, daemon=True).start()

    def _update_table(self):
        """Update token table"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add tokens
        for token in self.tokens:
            serial = token.get('serialNumber', '')
            manufacturer = token.get('manufacturer', '')
            model = token.get('model', '')
            hash_func = token.get('hashFunction', '')
            time_interval = token.get('timeIntervalInSeconds', 30)
            status = token.get('status', '')

            assigned_to = token.get('assignedTo', {})
            user_name = assigned_to.get('displayName', 'Unassigned') if assigned_to else 'Unassigned'

            last_used = token.get('lastUsedDateTime', 'Never')

            values = (
                serial,
                f"{manufacturer}/{model}",
                hash_func,
                f"{time_interval}s",
                user_name,
                status,
                last_used
            )

            # Store token data in item
            item_id = self.tree.insert("", "end", values=values, tags=(token.get('id'),))

    def _show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if not item:
            return

        self.tree.selection_set(item)
        token = self._get_selected_token()

        if not token:
            return

        # Create context menu
        menu = tk.Menu(self, tearoff=0)

        assigned_to = token.get('assignedTo')
        status = token.get('status', '')

        if not assigned_to:
            # Unassigned token
            menu.add_command(label="Assign to User", command=self._assign_token)
            menu.add_separator()
            menu.add_command(label="Delete Token", command=self._delete_token)
        else:
            # Assigned token
            if status != 'activated':
                menu.add_command(label="Activate", command=self._activate_token)

            menu.add_command(label="Unassign", command=self._unassign_token)

        menu.post(event.x_root, event.y_root)

    def _on_double_click(self, event):
        """Handle double-click on token"""
        token = self._get_selected_token()
        if not token:
            return

        assigned_to = token.get('assignedTo')
        status = token.get('status', '')

        if not assigned_to:
            self._assign_token()
        elif status != 'activated':
            self._activate_token()

    def _get_selected_token(self) -> Dict[str, Any]:
        """Get currently selected token"""
        selection = self.tree.selection()
        if not selection:
            return None

        item = selection[0]
        tags = self.tree.item(item, 'tags')
        if not tags:
            return None

        token_id = tags[0]

        # Find token in list
        for token in self.tokens:
            if token.get('id') == token_id:
                return token

        return None

    def _assign_token(self):
        """Open assign dialog"""
        token = self._get_selected_token()
        if not token:
            return

        AssignDialog(
            self,
            self.api_client,
            token.get('id'),
            token.get('serialNumber'),
            self._load_tokens
        )

    def _activate_token(self):
        """Open activate dialog"""
        token = self._get_selected_token()
        if not token:
            return

        assigned_to = token.get('assignedTo', {})
        if not assigned_to:
            self._show_error("Token must be assigned first")
            return

        ActivateDialog(
            self,
            self.api_client,
            token.get('id'),
            assigned_to.get('id'),
            token.get('serialNumber'),
            assigned_to.get('displayName', ''),
            self._load_tokens
        )

    def _unassign_token(self):
        """Unassign token from user"""
        token = self._get_selected_token()
        if not token:
            return

        assigned_to = token.get('assignedTo', {})
        if not assigned_to:
            return

        if not messagebox.askyesno("Confirm", "Unassign this token?"):
            return

        self.status_label.configure(text="Unassigning token...", text_color="blue")

        def unassign():
            try:
                self.api_client.unassign_token(assigned_to.get('id'), token.get('id'))
                self.after(0, lambda: self.status_label.configure(
                    text="Token unassigned successfully",
                    text_color="green"
                ))
                self.after(0, self._load_tokens)

            except GraphAPIError as e:
                self.after(0, lambda: self._show_error(f"Unassign failed: {e.message}"))

        threading.Thread(target=unassign, daemon=True).start()

    def _delete_token(self):
        """Delete token permanently"""
        token = self._get_selected_token()
        if not token:
            return

        if not messagebox.askyesno("Confirm", "Delete this token permanently? This cannot be undone."):
            return

        self.status_label.configure(text="Deleting token...", text_color="blue")

        def delete():
            try:
                self.api_client.delete_token(token.get('id'))
                self.after(0, lambda: self.status_label.configure(
                    text="Token deleted successfully",
                    text_color="green"
                ))
                self.after(0, self._load_tokens)

            except GraphAPIError as e:
                self.after(0, lambda: self._show_error(f"Delete failed: {e.message}"))

        threading.Thread(target=delete, daemon=True).start()

    def _open_import_dialog(self):
        """Open CSV import dialog"""
        if not self.api_client:
            self._show_error("Please load tokens first")
            return

        ImportCSVDialog(self, self.api_client, self._load_tokens)

    def _clear_session(self):
        """Clear session and restart"""
        if messagebox.askyesno("Confirm", "Clear all settings and logout?"):
            self.config.clear_credentials()
            self.destroy()
            # Could restart app here

    def _show_error(self, message: str):
        """Show error message"""
        messagebox.showerror("Error", message)
