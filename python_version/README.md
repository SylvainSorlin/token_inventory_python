# Token Inventory — MSAL Delegated Edition

Python/Tkinter desktop app for managing hardware OATH tokens (Token2 C203, etc.) in Microsoft Entra ID, using **interactive delegated authentication via MSAL**.

No client secret. No application permissions. Every Graph API call runs under the identity of the signed-in technician, with full Conditional Access, MFA, and audit trail.

## Architecture

```
token_inventory_msal/
├── main.py                 # Entry point
├── config.py               # Settings persistence (~/.token_inventory_msal/)
├── auth.py                 # MSAL PublicClientApplication + token cache
├── api/
│   ├── graph_api.py        # Graph client (inventory, assign, activate, CSV import)
│   └── totp.py             # TOTP code generator (for auto-activation)
├── gui/
│   ├── main_window.py      # Main window (toolbar + treeview + context menus)
│   ├── settings_dialog.py  # Tenant ID + Client ID form (no secret)
│   └── dialogs.py          # Assign / Activate / Import CSV dialogs
├── requirements.txt        # msal, requests, pyotp
├── build_exe.py            # PyInstaller → standalone .exe
└── run.bat                 # Windows quick launcher
```

**Key design decisions:**

- **MSAL `PublicClientApplication`** — no client secret at all. Authentication uses `authorization_code` + PKCE handled internally by MSAL. The library opens the system browser for sign-in and listens on a local port for the callback.
- **Token cache on disk** (`msal_cache.bin`) — MSAL's `SerializableTokenCache` stores the access and refresh tokens locally. On next launch, `acquire_token_silent` reuses the refresh token without opening the browser again (up to 90 days). Cache is cleared on sign-out.
- **`https://graph.microsoft.com/.default`** as the only scope — since the app registration already declares and has admin-consent for the specific delegated permissions, `.default` tells Entra "give me everything consented on this app". No need to list individual scopes in the code.
- **Standard tkinter** — no `customtkinter` dependency. Works on Windows, macOS, Linux with the stock Python distribution.
- **Same Graph API layer** as the upstream project — `fetch_tokens`, `assign_token`, `activate_token`, `import_csv`, etc. all use the beta `hardwareOathDevices` endpoint. The only difference is how the bearer token is obtained.

## Entra app registration setup

1. **New registration** → single tenant, no redirect URI yet.
2. **Authentication blade:**
   - Add platform → **Mobile and desktop applications** (this is what MSAL's `acquire_token_interactive` expects)
   - Add redirect URI: `http://localhost`
   - Set **Allow public client flows = Yes**
3. **API permissions** → Microsoft Graph → **Delegated** (not Application):
   - `Policy.ReadWrite.AuthenticationMethod`
   - `UserAuthenticationMethod.ReadWrite.All`
   - `User.Read.All`
   - `Directory.Read.All`
   - `offline_access` (for refresh tokens — usually auto-included)
4. **Grant admin consent** — Privileged Role Administrator or Global Administrator, one time.
5. **Certificates & secrets** → leave empty. Nothing.
6. Copy **Application (client) ID** and **Directory (tenant) ID** from the Overview page.

## Install and run

### Option A: from source (recommended for dev/test)

```bash
# Python 3.10+
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Or on Windows: double-click `run.bat`.

### Option B: standalone .exe

```bash
pip install pyinstaller
python build_exe.py
# Output: dist/TokenInventory.exe
```

## First launch

1. The app opens with a welcome screen → click **Configure app settings**.
2. Enter the **Tenant ID** and **Client ID** from your Entra app registration. No secret.
3. Click **Save**. The app opens your system browser to the Microsoft sign-in page.
4. Authenticate with your Entra account (MFA, CA policies apply as usual).
5. The browser shows "Authentication complete" → close the tab → back in the app, the token inventory loads automatically.
6. Top-right shows **Signed in as `your.name@contoso.com`**.

On subsequent launches, sign-in is silent (refresh token) — the browser won't open unless the token has expired (90 days) or been revoked.

## Usage

### View inventory

The main table shows all hardware OATH tokens in the tenant, with serial number, device model, hash function, assigned user, status (available / assigned / activated), and last used date. Click any column header to sort.

### Assign a token

Right-click an unassigned token → **Assign to user…** → search by name or UPN → select → click **Assign**.

### Activate a token

Right-click an assigned (but not activated) token → **Activate…** → two options:
- **Manual**: press the button on the physical token, read the 6-digit code, type it in.
- **Auto-generate**: paste the token's base32 secret key → the app computes the current TOTP code and fills it in automatically.

### Import CSV (bulk)

Click **📥 Import CSV** → paste a Token2 CSV → choose the mode:
- **Import only**: creates the tokens in the tenant inventory (unassigned).
- **Import & Assign**: creates + assigns to the user in the `upn` column.
- **Import, Assign & Activate**: does all three in one shot (auto-computes the OTP from the secret key). This is the fastest mode for bulk deployment.

CSV format:
```csv
upn,serial number,secret key,timeinterval,manufacturer,model
alice@contoso.com,GALT11420104,C2dE3fH4iJ5kL6mN7oP1qR2sT3uV4w,30,Token2,C203
```

### Sign out

Click **Sign out** → clears the MSAL token cache and removes the account locally. Does not revoke the refresh token on the Microsoft side (that requires a separate admin action in Entra if needed).

## Role requirements

The signed-in user must hold the appropriate Entra role:

| Action | Minimum role |
|---|---|
| Provision tokens (import into inventory) | Authentication Policy Administrator |
| Assign / activate / unassign tokens | Authentication Administrator |
| Delete tokens from inventory | Authentication Policy Administrator |
| Search users | User.Read.All (delegated permission, no role needed) |

If the account lacks the required role, Graph returns HTTP 403 and the app displays the error.

## Security

- **No client secret** stored anywhere — not in config, not in memory, not on disk. The MSAL `PublicClientApplication` uses PKCE internally, which is a per-session ephemeral secret.
- **Refresh token** is stored in `~/.token_inventory_msal/msal_cache.bin`. This file is the most sensitive artifact on disk: anyone who obtains it can impersonate the technician (within the scope of the delegated permissions) until the token expires. Mitigations:
  - The file is user-readable only (created under the user's home directory).
  - Sign out clears and deletes the file.
  - Entra's Conditional Access policies (device compliance, named locations) apply to the refresh token at renewal time.
  - On shared workstations, each technician should use a separate OS user account.
- **Audit trail**: every Graph API call appears in the Entra audit logs under the technician's real UPN, not a service principal. Searching "who assigned token X?" gives a direct answer.
- **Conditional Access**: MFA, device compliance, named locations, risk-based policies all apply — the sign-in goes through the standard Entra evaluation pipeline.

## Differences from the upstream project

| | Upstream (SylvainSorlin) | This fork |
|---|---|---|
| Auth flow | `client_credentials` (app secret) | `authorization_code` + PKCE via MSAL (interactive) |
| UI framework | `customtkinter` | Standard `tkinter` (no extra dependency) |
| Client secret | Required, stored in config.json | Not used, not stored anywhere |
| Graph permissions | Application | Delegated |
| Audit identity | Service principal | Human user (UPN) |
| Token cache | N/A (new token per session) | MSAL `SerializableTokenCache` on disk (silent refresh for 90 days) |
| Conditional Access | Doesn't apply (app flow) | Fully applies (user flow) |
| Dependencies | `customtkinter`, `requests`, `pyotp`, `Pillow` | `msal`, `requests`, `pyotp` |

## Troubleshooting

**Browser opens but sign-in fails with AADSTS70011**
The app registration is missing required delegated scopes or admin consent hasn't been granted. Check API permissions in Entra.

**Browser opens but sign-in fails with AADSTS7000218**
"Allow public client flows" is not set to Yes in the app registration's Authentication blade.

**HTTP 403 on every Graph call**
Your account lacks the required Entra role (Authentication Administrator or Authentication Policy Administrator). The delegated permissions are granted to the app, but the role determines what the *user* is allowed to do through those permissions.

**"Sign-in failed: User cancelled"**
The user closed the browser tab before completing authentication. Click Refresh to try again.

**Token cache doesn't refresh (browser opens every time)**
The `offline_access` scope may not be consented. Add it to the app's delegated permissions and re-consent.

## License

Same license as the upstream project.
