"""
Configuration management for Token Inventory
Stores credentials securely in local JSON file
"""
import json
import os
from pathlib import Path
from typing import Optional

class Config:
    """Manages application configuration"""

    def __init__(self):
        self.config_dir = Path.home() / ".token_inventory"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
        self._config = self._load_config()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)

    def _load_config(self) -> dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)

    def set(self, key: str, value):
        """Set configuration value"""
        self._config[key] = value
        self._save_config()

    # Convenience properties
    @property
    def tenant_id(self) -> Optional[str]:
        return self.get('tenant_id')

    @tenant_id.setter
    def tenant_id(self, value: str):
        self.set('tenant_id', value)

    @property
    def client_id(self) -> Optional[str]:
        return self.get('client_id')

    @client_id.setter
    def client_id(self, value: str):
        self.set('client_id', value)

    @property
    def client_secret(self) -> Optional[str]:
        return self.get('client_secret')

    @client_secret.setter
    def client_secret(self, value: str):
        self.set('client_secret', value)

    @property
    def show_logs(self) -> bool:
        return self.get('show_logs', True)

    @show_logs.setter
    def show_logs(self, value: bool):
        self.set('show_logs', value)

    def has_credentials(self) -> bool:
        """Check if all required credentials are set"""
        return all([self.tenant_id, self.client_id, self.client_secret])

    def clear_credentials(self):
        """Clear all stored credentials"""
        self._config = {}
        self._save_config()
