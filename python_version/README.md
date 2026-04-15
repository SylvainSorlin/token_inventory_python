# TOTP Token Inventory - Python Edition

Modern, lightweight Python application for managing Microsoft Entra ID hardware OATH tokens.

## 🚀 Features

- **Modern GUI** with CustomTkinter
- **Lightweight** - Small footprint, fast startup
- **Standalone EXE** - No dependencies needed
- **Full functionality** - Import, Assign, Activate, Manage tokens
- **Automatic TOTP generation** - Built-in code generation
- **CSV Import** - Bulk import with multiple modes

## 📦 Installation

### Option 1: Run from source

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Option 2: Build standalone executable

```bash
# Install build tools
pip install pyinstaller

# Build executable
python build_exe.py

# Run the exe
dist/TokenInventory.exe
```

## 🎯 Requirements

### System Requirements
- Python 3.11+
- Windows 10/11 (or Linux/Mac for source)
- Internet connection

### Microsoft Graph API Permissions

Required permissions in Azure AD App Registration:
- `Policy.ReadWrite.AuthenticationMethod`
- `UserAuthenticationMethod.ReadWrite.All`
- `User.Read.All`
- `Directory.Read.All`

**Don't forget to grant admin consent!**

## 📖 Usage

### Initial Setup

1. Launch the application
2. Click "Open Settings"
3. Enter your Microsoft Graph credentials:
   - Tenant ID
   - Client ID
   - Client Secret
4. Click "Save Settings"

### Managing Tokens

- **View Tokens**: Main table shows all tokens
- **Refresh**: Click refresh button to reload
- **Assign Token**: Right-click unassigned token → Assign
- **Activate Token**: Right-click assigned token → Activate
- **Unassign**: Right-click assigned token → Unassign
- **Delete**: Right-click unassigned token → Delete

### CSV Import

1. Click "Import CSV" button
2. Select import mode:
   - **Import Only**: Just create tokens
   - **Import & Assign**: Create and assign to users
   - **Import, Assign & Activate**: Full automation
3. Paste CSV data with format:
   ```
   upn,serial number,secret key,timeinterval,manufacturer,model
   user@domain.com,1100000,JBSWY3DPEHPK3PXP,30,Token2,miniOTP-1
   ```
4. Click "Import"

## 🏗️ Project Structure

```
python_version/
├── main.py                 # Entry point
├── config.py              # Configuration management
├── api/
│   ├── graph_api.py       # Microsoft Graph client
│   └── totp.py           # TOTP generation
├── gui/
│   ├── main_window.py    # Main window
│   ├── settings_window.py # Settings dialog
│   └── dialogs.py        # Operation dialogs
├── requirements.txt       # Dependencies
├── build_exe.py          # Build script
└── README.md             # This file
```

## 🔧 Building for Distribution

### Standard Build (includes Python)
```bash
python build_exe.py
```
Result: ~15-20 MB executable

### Optimized Build (smaller size)
```bash
# Use UPX compression
pip install pyinstaller[compression]

# Or use Nuitka for better optimization
pip install nuitka
python -m nuitka --onefile --windows-disable-console main.py
```
Result: ~5-10 MB executable

## 🆚 Comparison with PHP Version

| Feature | PHP Version | Python Version |
|---------|-------------|----------------|
| Size | Requires server | Single 15MB .exe |
| Deployment | Web server needed | Double-click to run |
| UI | Bootstrap web | Native desktop GUI |
| Speed | Page loads | Instant response |
| Offline | No | Config only |

## 🐛 Troubleshooting

### "No module named customtkinter"
```bash
pip install customtkinter
```

### "Authentication failed"
- Check Tenant ID, Client ID, Client Secret
- Verify API permissions are granted
- Check admin consent is approved

### "Permission denied"
- Go to Azure Portal
- App Registrations → Your App
- API Permissions → Grant admin consent

### Build fails
```bash
# Clear cache
pip cache purge

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Try build again
python build_exe.py
```

## 📝 License

Same as original PHP version

## 🙏 Credits

Python version based on the original PHP TOTP Token Inventory by Token2

## 🔗 Links

- Original PHP version: [GitHub Repository]
- Microsoft Graph API: https://graph.microsoft.com
- CustomTkinter: https://github.com/TomSchimansky/CustomTkinter
