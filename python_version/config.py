"""
Configuration management — stores app settings locally (no secrets).
"""
import json
from pathlib import Path
from typing import Optional


class Config:
    """Manages Tenant ID, Client ID and UI preferences. No client secret."""

    def __init__(self):
        self.config_dir = Path.home() / ".token_inventory_msal"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)
        self._data = self._load()

    # ── persistence ──────────────────────────────────────────────────

    def _load(self) -> dict:
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text())
            except Exception:
                return {}
        return {}

    def _save(self):
        self.config_file.write_text(json.dumps(self._data, indent=2))

    # ── accessors ────────────────────────────────────────────────────

    @property
    def tenant_id(self) -> Optional[str]:
        return self._data.get("tenant_id")

    @tenant_id.setter
    def tenant_id(self, value: str):
        self._data["tenant_id"] = value
        self._save()

    @property
    def client_id(self) -> Optional[str]:
        return self._data.get("client_id")

    @client_id.setter
    def client_id(self, value: str):
        self._data["client_id"] = value
        self._save()

    @property
    def show_logs(self) -> bool:
        return self._data.get("show_logs", True)

    @show_logs.setter
    def show_logs(self, value: bool):
        self._data["show_logs"] = value
        self._save()

    def is_configured(self) -> bool:
        return bool(self.tenant_id and self.client_id)

    def clear(self):
        self._data = {}
        self._save()

    @property
    def cache_path(self) -> Path:
        """Path for the MSAL token cache (separate from config)."""
        return self.config_dir / "msal_cache.bin"
