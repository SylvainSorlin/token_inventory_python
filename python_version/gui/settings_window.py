"""
Settings Window
Configuration dialog for Microsoft Graph credentials
"""
import customtkinter as ctk
from typing import Callable

class SettingsWindow(ctk.CTkToplevel):
    """Settings window for credentials configuration"""

    def __init__(self, parent, config, on_save: Callable = None):
        super().__init__(parent)

        self.config = config
        self.on_save = on_save

        self.title("Settings")
        self.geometry("500x400")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._load_values()

    def _create_widgets(self):
        """Create settings form widgets"""

        # Title
        title = ctk.CTkLabel(
            self,
            text="Microsoft Graph Credentials",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Tenant ID
        ctk.CTkLabel(form_frame, text="Tenant ID:", anchor="w").pack(pady=(10, 0), padx=10, fill="x")
        self.tenant_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter Tenant ID")
        self.tenant_entry.pack(pady=(0, 10), padx=10, fill="x")

        # Client ID
        ctk.CTkLabel(form_frame, text="Client ID:", anchor="w").pack(pady=(0, 0), padx=10, fill="x")
        self.client_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter Client ID")
        self.client_entry.pack(pady=(0, 10), padx=10, fill="x")

        # Client Secret
        ctk.CTkLabel(form_frame, text="Client Secret:", anchor="w").pack(pady=(0, 0), padx=10, fill="x")
        self.secret_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter Client Secret", show="*")
        self.secret_entry.pack(pady=(0, 10), padx=10, fill="x")

        # Show logs checkbox
        self.show_logs_var = ctk.BooleanVar(value=True)
        self.show_logs_check = ctk.CTkCheckBox(
            form_frame,
            text="Show operation logs",
            variable=self.show_logs_var
        )
        self.show_logs_check.pack(pady=10, padx=10, anchor="w")

        # Info label
        info_text = (
            "Required API permissions:\n"
            "• Policy.ReadWrite.AuthenticationMethod\n"
            "• UserAuthenticationMethod.ReadWrite.All\n"
            "• User.Read.All\n"
            "• Directory.Read.All"
        )
        info_label = ctk.CTkLabel(
            form_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left"
        )
        info_label.pack(pady=10, padx=10, anchor="w")

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, padx=20, fill="x")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(side="right", padx=5)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Settings",
            command=self._save_settings
        )
        save_btn.pack(side="right", padx=5)

        clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear All",
            command=self._clear_settings,
            fg_color="red",
            hover_color="darkred"
        )
        clear_btn.pack(side="left", padx=5)

    def _load_values(self):
        """Load current configuration values"""
        if self.config.tenant_id:
            self.tenant_entry.insert(0, self.config.tenant_id)
        if self.config.client_id:
            self.client_entry.insert(0, self.config.client_id)
        if self.config.client_secret:
            self.secret_entry.insert(0, self.config.client_secret)

        self.show_logs_var.set(self.config.show_logs)

    def _save_settings(self):
        """Save settings and close"""
        tenant = self.tenant_entry.get().strip()
        client = self.client_entry.get().strip()
        secret = self.secret_entry.get().strip()

        if not all([tenant, client, secret]):
            self._show_error("All fields are required!")
            return

        self.config.tenant_id = tenant
        self.config.client_id = client
        self.config.client_secret = secret
        self.config.show_logs = self.show_logs_var.get()

        if self.on_save:
            self.on_save()

        self.destroy()

    def _clear_settings(self):
        """Clear all settings"""
        if self._confirm("Are you sure you want to clear all settings?"):
            self.config.clear_credentials()
            self.tenant_entry.delete(0, 'end')
            self.client_entry.delete(0, 'end')
            self.secret_entry.delete(0, 'end')

            if self.on_save:
                self.on_save()

    def _show_error(self, message: str):
        """Show error message"""
        error_window = ctk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("300x150")
        error_window.transient(self)
        error_window.grab_set()

        ctk.CTkLabel(
            error_window,
            text=message,
            wraplength=250,
            font=ctk.CTkFont(size=12)
        ).pack(pady=20, padx=20)

        ctk.CTkButton(
            error_window,
            text="OK",
            command=error_window.destroy
        ).pack(pady=10)

    def _confirm(self, message: str) -> bool:
        """Show confirmation dialog"""
        result = [False]

        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm")
        confirm_window.geometry("350x150")
        confirm_window.transient(self)
        confirm_window.grab_set()

        ctk.CTkLabel(
            confirm_window,
            text=message,
            wraplength=300,
            font=ctk.CTkFont(size=12)
        ).pack(pady=20, padx=20)

        def on_yes():
            result[0] = True
            confirm_window.destroy()

        button_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="No",
            command=confirm_window.destroy,
            fg_color="gray",
            width=100
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Yes",
            command=on_yes,
            width=100
        ).pack(side="left", padx=5)

        self.wait_window(confirm_window)
        return result[0]
