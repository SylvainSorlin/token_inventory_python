# 🚀 Quick Start Guide

Get up and running in 5 minutes!

## Windows

### Option A: Run from Source (Recommended for development)

```batch
REM 1. Run setup script
setup_dev.bat

REM 2. Activate virtual environment
venv\Scripts\activate

REM 3. Run application
python main.py
```

### Option B: Build Standalone EXE

```batch
REM 1. Install PyInstaller
pip install pyinstaller

REM 2. Build
python build_exe.py

REM 3. Run
dist\TokenInventory.exe
```

## Linux/Mac

### Run from Source

```bash
# 1. Run setup script
chmod +x setup_dev.sh
./setup_dev.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run application
python main.py
```

## First Launch

1. **Open Settings** when prompted
2. **Enter credentials**:
   - Tenant ID: Your Azure AD tenant ID
   - Client ID: Your app registration client ID
   - Client Secret: Your app registration secret
3. **Click Save**
4. Tokens will load automatically!

## Azure Setup (If not done)

### 1. Create App Registration

1. Go to Azure Portal → Azure Active Directory
2. App Registrations → New registration
3. Name: "Token Inventory"
4. Supported account types: Single tenant
5. Redirect URI: Not needed
6. Click **Register**

### 2. Add API Permissions

1. Your App → API permissions
2. Add permission → Microsoft Graph → Application permissions
3. Add these permissions:
   - `Policy.ReadWrite.AuthenticationMethod`
   - `UserAuthenticationMethod.ReadWrite.All`
   - `User.Read.All`
   - `Directory.Read.All`
4. **Grant admin consent** ← IMPORTANT!

### 3. Create Client Secret

1. Your App → Certificates & secrets
2. New client secret
3. Description: "Token Inventory"
4. Expires: Choose duration
5. Click Add
6. **Copy the secret value** ← You need this!

### 4. Get IDs

- **Tenant ID**: App overview page
- **Client ID**: App overview page  
- **Client Secret**: From step 3

## Quick Test

### CSV Import Test

Copy this test data:

```csv
upn,serial number,secret key,timeinterval,manufacturer,model
user@yourdomain.com,TEST001,JBSWY3DPEHPK3PXP,30,Token2,Test-1
```

1. Click **Import CSV**
2. Select **Import, Assign & Activate**
3. Paste test data
4. Click **Import**

✅ Token should be imported, assigned, and activated!

## Troubleshooting

### "Authentication failed"
- ✅ Check Tenant ID is correct
- ✅ Check Client ID is correct
- ✅ Check Client Secret is not expired
- ✅ Verify you copied the secret VALUE, not the ID

### "Permission denied"
- ✅ Check all 4 API permissions are added
- ✅ **Grant admin consent** in Azure Portal
- ✅ Wait 5 minutes for permissions to propagate

### "No module named customtkinter"
```bash
pip install customtkinter
```

### Build fails
```bash
pip cache purge
pip install -r requirements.txt --force-reinstall
python build_exe.py
```

## Next Steps

- ✅ Import tokens from CSV
- ✅ Assign tokens to users
- ✅ Activate tokens automatically
- ✅ Manage token lifecycle

## Support

- Check main README.md for detailed documentation
- Review error messages carefully
- Verify Azure permissions are correct
- Test with a single token first

---

**Ready to go? Launch the app!**

Windows: `python main.py`  
Linux/Mac: `python main.py`  
Standalone: `dist\TokenInventory.exe`
