"""
MSAL-based delegated authentication.

Uses PublicClientApplication (no client secret, no certificate).
Token acquisition: acquire_token_silent → acquire_token_interactive (browser).
Token cache persisted to disk so the user isn't prompted at every launch.
"""
import json
import atexit
import os
import stat
from typing import Optional

import msal

from config import Config

# The single scope triggers "give me everything consented on this app".
# The actual granular permissions are declared in the Entra app registration.
SCOPES = ["https://graph.microsoft.com/.default"]


class AuthManager:
    """Manages the MSAL public-client flow and token lifecycle."""

    def __init__(self, config: Config):
        self._config = config
        self._app: Optional[msal.PublicClientApplication] = None
        self._cache = msal.SerializableTokenCache()
        self._account = None
        self._load_cache()

    # ── cache persistence ────────────────────────────────────────────

    def _load_cache(self):
        path = self._config.cache_path
        if path.exists():
            self._cache.deserialize(path.read_text())
        atexit.register(self._save_cache)

    def _save_cache(self):
        if self._cache.has_state_changed:
            cache_file = self._config.cache_path
            cache_file.write_text(self._cache.serialize())
            # Sécuriser les permissions : lisible/modifiable par le propriétaire uniquement
            os.chmod(cache_file, stat.S_IRUSR | stat.S_IWUSR)  # 0o600

    # ── MSAL app ─────────────────────────────────────────────────────

    def _ensure_app(self):
        if self._app is None:
            if not self._config.is_configured():
                raise RuntimeError("Tenant ID and Client ID must be set in Settings.")
            authority = f"https://login.microsoftonline.com/{self._config.tenant_id}"
            self._app = msal.PublicClientApplication(
                client_id=self._config.client_id,
                authority=authority,
                token_cache=self._cache,
            )

    def reset(self):
        """Force recreation of the MSAL app (after settings change)."""
        self._app = None
        self._account = None

    # ── token acquisition ────────────────────────────────────────────

    def get_access_token(self) -> str:
        """
        Return a valid access token.

        1. Try silent (cached / refresh-token).
        2. Fall back to interactive browser sign-in.
        """
        self._ensure_app()

        # Prefer the previously used account
        accounts = self._app.get_accounts()
        if accounts:
            self._account = accounts[0]

        # Silent first
        if self._account:
            result = self._app.acquire_token_silent(
                scopes=SCOPES,
                account=self._account,
            )
            if result and "access_token" in result:
                return result["access_token"]

        # Interactive fallback — opens the system browser
        result = self._app.acquire_token_interactive(
            scopes=SCOPES,
            prompt="select_account",
        )

        if "access_token" not in result:
            error = result.get("error_description") or result.get("error") or "Unknown auth error"
            raise RuntimeError(f"Sign-in failed: {error}")

        # Remember account for silent calls
        accounts = self._app.get_accounts()
        if accounts:
            self._account = accounts[0]

        self._save_cache()
        return result["access_token"]

    # ── account info ─────────────────────────────────────────────────

    @property
    def signed_in_user(self) -> Optional[str]:
        """UPN of the currently cached user, or None."""
        if self._account:
            return self._account.get("username")
        self._ensure_app()
        accounts = self._app.get_accounts()
        if accounts:
            self._account = accounts[0]
            return self._account.get("username")
        return None

    def sign_out(self):
        """Remove all cached accounts (local only — doesn't revoke tokens)."""
        self._ensure_app()
        for acct in self._app.get_accounts():
            self._app.remove_account(acct)
        self._account = None
        self._save_cache()
        # Also delete the cache file
        if self._config.cache_path.exists():
            self._config.cache_path.unlink()
