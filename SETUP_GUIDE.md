# The Notebook Concert - Complete Setup Guide

## ✅ Your App is Now Running!

The application is running at: **http://localhost:8501**

---

## 🚀 Quick Start

### If You See "Access is Denied" Error

**Solution:** Use this command instead:
```powershell
python -m streamlit run app.py
```

Instead of:
```powershell
streamlit run app.py
```

---

## 📋 Prerequisites Checklist

Before running the app, make sure you have:

- [ ] **Python 3.12** installed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Google Service Account credentials
- [ ] Google Sheet created and shared with service account
- [ ] `secrets.toml` configured

---

## 🔧 Step-by-Step Setup

### Step 1: Install Dependencies

```powershell
cd "C:\Users\RahulTejwani\Downloads\My_Files\ticketing app"
pip install -r requirements.txt
```

**Expected output:** All packages installed successfully

---

### Step 2: Configure Google Sheets

1. **Create Google Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project: "Notebook Concert"
   - Enable APIs:
     - Google Sheets API
     - Google Drive API
   - Create Service Account (Credentials → Service Account)
   - Download JSON key

2. **Create Google Sheet:**
   - Go to [Google Sheets](https://docs.google.com/spreadsheets)
   - Create new sheet: "Notebook Concert Tickets"
   - Share with service account email (from JSON file)
   - Copy the sheet URL

---

### Step 3: Configure Secrets

**On Windows:**
```
C:\Users\YourUsername\AppData\Roaming\.streamlit\secrets.toml
```

**Example `secrets.toml`:**
```toml
[google_service_account]
type = "service_account"
project_id = "notebook-concert-123"
private_key_id = "abc123def456"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "concert-service@notebook-concert-123.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
admin_password = "YourSecurePassword123"
```

---

### Step 4: Run the Application

```powershell
cd "C:\Users\RahulTejwani\Downloads\My_Files\ticketing app"
python -m streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.4:8501
```

Open browser to: **http://localhost:8501**

---

## 📖 Using the Application

### 🎫 Booking Mode (Default)

1. Enter your details:
   - Full Name
   - Email Address
   - Phone Number
   - UTR/Transaction ID

2. Click "Submit Booking"

3. You'll see a QR code - **screenshot it!**

4. Your ticket status: "Pending" (waiting for admin approval)

---

### 🔐 Admin Mode

1. Select "Admin" from sidebar
2. Enter password (configured in `secrets.toml`)
3. Choose from three tabs:

#### Tab 1: Approve Tickets
- View all pending bookings
- Click "✅ Approve" to validate tickets
- Ticket status changes from "Pending" to "Valid"

#### Tab 2: Scan QR
**Two options:**

**Option A: Manual UUID Entry (Recommended for Windows)**
- Type the UUID from the QR code ticket
- System checks them in automatically

**Option B: QR Scanning (if pyzbar works)**
- Click camera button
- Scan the QR code
- Automatic check-in with status confirmation

#### Tab 3: All Tickets
- View complete database
- See all ticket statuses
- Monitor total attendance

---

## 🐛 Troubleshooting

### Problem 1: "Access is Denied"

**Solution:**
```powershell
python -m streamlit run app.py
```

Instead of `streamlit run app.py`

---

### Problem 2: "Credentials not found in secrets"

**Check:**
1. Is `secrets.toml` in the right location?
   - Windows: `%APPDATA%\.streamlit\secrets.toml`
2. Does it have `[google_service_account]` section?
3. Restart the app after creating secrets

**Fix:**
```powershell
# Create folder if it doesn't exist
mkdir %APPDATA%\.streamlit

# Then create/edit secrets.toml in that folder
```

---

### Problem 3: "Sheet URL not found"

**Check:**
- `secrets.toml` has `sheet_url = "https://..."`
- URL is correct and accessible
- Sheet is shared with service account email

---

### Problem 4: "QR Scanning Not Working"

**This is normal on Windows.** Use Option A (Manual UUID Entry) instead:
- Look at the QR code
- Find the UUID printed below it
- Enter manually in the "Scan QR" section

---

### Problem 5: Import Errors

**Error:** `ModuleNotFoundError: No module named 'streamlit'`

**Solution:**
```powershell
pip install -r requirements.txt
```

---

### Problem 6: Port Already in Use

**Error:** `Address already in use: ('127.0.0.1', 8501)`

**Solution:**
```powershell
# Kill the process using port 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Or use different port
streamlit run app.py --server.port 8502
```

---

## 📁 File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `sheets_helper.py` | Google Sheets API integration |
| `qr_helper.py` | QR code generation |
| `requirements.txt` | Python dependencies |
| `secrets_template.toml` | Template for secrets configuration |
| `README.md` | Full documentation |
| `ADMIN_PASSWORD_GUIDE.md` | Admin password explanation |
| `SETUP_GUIDE.md` | This file |

---

## 🔒 Security Checklist

- [ ] `secrets.toml` is in `%APPDATA%\.streamlit\` (not in project folder)
- [ ] `secrets.toml` is NOT committed to Git
- [ ] Admin password is strong (12+ chars, mixed case, numbers)
- [ ] Google Sheet only shared with service account
- [ ] Private key in secrets.toml includes `\n` for line breaks

---

## 📱 Testing the Workflow

1. **Create a test booking:**
   - Select "Booking" mode
   - Fill form with test data
   - Submit
   - Take note of the UUID shown

2. **Approve as admin:**
   - Select "Admin" mode
   - Enter password
   - Go to "Approve Tickets"
   - Approve your test booking

3. **Check in:**
   - Go to "Scan QR" tab
   - Enter the UUID from step 1
   - Confirm check-in success

---

## 🎯 Common Commands

```powershell
# Run the app
python -m streamlit run app.py

# Run on different port
python -m streamlit run app.py --server.port 8502

# Disable telemetry
set STREAMLIT_LOGGER_LEVEL=error

# Run in headless mode (no browser)
streamlit run app.py --logger.level=error --client.showErrorDetails=false
```

---

## ✨ Next Steps

1. ✅ App is running at http://localhost:8501
2. Create test bookings in Booking Mode
3. Approve tickets as Admin
4. Test check-in functionality
5. Customize admin password and UI if needed
6. Deploy when ready!

---

## 📞 Still Having Issues?

1. Check this file first
2. Review `README.md` for detailed info
3. Check console output for error messages
4. Verify all configuration files are correct

**Happy ticketing! 🎵**
