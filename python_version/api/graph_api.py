"""
Microsoft Graph API client for hardware OATH token management.
Gets bearer tokens from AuthManager (delegated, no secret).
"""
import csv
from io import StringIO
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

import requests

from auth import AuthManager
from .totp import generate_totp_code, validate_base32_secret

GRAPH_BETA = "https://graph.microsoft.com/beta"
GRAPH_V1   = "https://graph.microsoft.com/v1.0"
INVENTORY  = f"{GRAPH_BETA}/directory/authenticationMethodDevices/hardwareOathDevices"


@dataclass
class GraphError(Exception):
    message: str
    status_code: Optional[int] = None
    details: Any = field(default=None)

    def __str__(self):
        return self.message


class GraphClient:
    """Stateless Graph client — token is fetched fresh via AuthManager."""

    def __init__(self, auth: AuthManager):
        self._auth = auth

    def _headers(self) -> dict:
        token = self._auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise_on_error(resp: requests.Response, context: str):
        if resp.ok:
            return
        try:
            body = resp.json()
            msg = body.get("error", {}).get("message", resp.text[:300])
        except Exception:
            msg = resp.text[:300]
        if resp.status_code in (401, 403) and "Insufficient privileges" in msg:
            msg = (
                f"{context}: missing Graph permissions.\n"
                "Required (Delegated):\n"
                "  • Policy.ReadWrite.AuthenticationMethod\n"
                "  • UserAuthenticationMethod.ReadWrite.All\n"
                "  • User.Read.All / Directory.Read.All"
            )
        raise GraphError(msg, resp.status_code)

    # ── inventory ────────────────────────────────────────────────────

    def fetch_tokens(self) -> List[Dict[str, Any]]:
        tokens, url = [], INVENTORY
        while url:
            r = requests.get(url, headers=self._headers(), timeout=30)
            self._raise_on_error(r, "Fetch tokens")
            data = r.json()
            tokens.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
        return tokens

    def import_token(self, token_data: dict) -> dict:
        r = requests.post(INVENTORY, headers=self._headers(), json=token_data, timeout=30)
        self._raise_on_error(r, "Import token")
        return r.json()

    def delete_token(self, token_id: str) -> bool:
        r = requests.delete(f"{INVENTORY}/{token_id}", headers=self._headers(), timeout=30)
        self._raise_on_error(r, "Delete token")
        return r.status_code in (200, 204)

    # ── assignment ───────────────────────────────────────────────────

    def assign_token(self, user_id: str, token_id: str) -> dict:
        url = f"{GRAPH_BETA}/users/{user_id}/authentication/hardwareOathMethods"
        r = requests.post(url, headers=self._headers(), json={"device": {"id": token_id}}, timeout=30)
        self._raise_on_error(r, "Assign token")
        return r.json() if r.text else {}

    def unassign_token(self, user_id: str, token_id: str) -> bool:
        url = f"{GRAPH_BETA}/users/{user_id}/authentication/hardwareOathMethods/{token_id}"
        r = requests.delete(url, headers=self._headers(), timeout=30)
        self._raise_on_error(r, "Unassign token")
        return r.status_code in (200, 204)

    def activate_token(self, user_id: str, token_id: str, code: str) -> bool:
        url = f"{GRAPH_BETA}/users/{user_id}/authentication/hardwareOathMethods/{token_id}/activate"
        r = requests.post(url, headers=self._headers(), json={"verificationCode": code}, timeout=30)
        self._raise_on_error(r, "Activate token")
        return r.status_code in (200, 204)

    # ── users ────────────────────────────────────────────────────────

    def search_users(self, query: str = "") -> List[Dict[str, Any]]:
        if query:
            flt = f"startswith(displayName,'{query}') or startswith(userPrincipalName,'{query}')"
            url = f"{GRAPH_V1}/users?$top=50&$filter={requests.utils.quote(flt)}"
        else:
            url = f"{GRAPH_V1}/users?$top=50"
        r = requests.get(url, headers=self._headers(), timeout=30)
        self._raise_on_error(r, "Search users")
        return r.json().get("value", [])

    # ── CSV bulk import ──────────────────────────────────────────────

    def import_csv(self, csv_text: str, mode: str = "import_assign_activate") -> Dict[str, Any]:
        """
        Bulk import from Token2 CSV.

        Modes: import_only | import_assign | import_assign_activate
        CSV columns: upn, serial number, secret key, timeinterval, manufacturer, model
        """
        results = {}
        reader = csv.DictReader(StringIO(csv_text))

        for row_num, row in enumerate(reader, start=2):
            serial  = row.get("serial number", "").strip()
            secret  = row.get("secret key", "").strip().upper().replace(" ", "")
            upn     = row.get("upn", "").strip()
            interval = int(row.get("timeinterval", 30))
            mfr     = row.get("manufacturer", "").strip()
            model   = row.get("model", "").strip()

            if not serial or not secret:
                results[serial or f"line_{row_num}"] = {"success": False, "error": "Missing serial/secret"}
                continue

            if mode in ("import_assign", "import_assign_activate") and not upn:
                results[serial] = {"success": False, "error": "UPN required for assignment"}
                continue

            valid, err = validate_base32_secret(secret)
            if not valid:
                results[serial] = {"success": False, "error": err}
                continue

            hash_fn = "hmacsha1" if len(secret) <= 32 else "hmacsha256"
            payload = {
                "displayName": f"{mfr} {model} - {serial}",
                "serialNumber": serial,
                "manufacturer": mfr,
                "model": model,
                "secretKey": secret,
                "timeIntervalInSeconds": interval,
                "hashFunction": hash_fn,
            }

            try:
                resp = self.import_token(payload)
                token_id = resp.get("id")
                entry = {"success": True, "token_id": token_id}

                if token_id and mode in ("import_assign", "import_assign_activate") and upn:
                    try:
                        self.assign_token(upn, token_id)
                        entry["assigned"] = True

                        if mode == "import_assign_activate":
                            code = generate_totp_code(secret, interval)
                            if code:
                                entry["activated"] = self.activate_token(upn, token_id, code)
                            else:
                                entry["activated"] = False
                                entry["activation_error"] = "TOTP generation failed"
                    except GraphError as e:
                        entry["assigned"] = False
                        entry["error"] = str(e)

                results[serial] = entry

            except GraphError as e:
                results[serial] = {"success": False, "error": str(e)}

        return results
