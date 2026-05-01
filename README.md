# The Notebook Concert - Ticketing System

A complete single-page Streamlit application that functions as both a ticket booking system and an admin scanner for The Notebook Concert event.

## Features

### 🎫 Booking Mode (Default)
- User-friendly form to collect attendee details (Name, Email, Phone)
- Ticket quantity selector with live total amount calculation
- Display UPI payment QR code for instant payment
- Input field for UTR/Transaction ID validation
- Generates one unique UUID and QR code per ticket
- Sends ticket QR codes by email and WhatsApp when delivery credentials are configured
- Saves booking data to Google Sheets with "Pending" status

### 🔐 Admin Mode (Password Protected)
- **Approve Tickets Tab**: View pending tickets and approve them (changes status to "Valid")
- **Scan QR Tab**: Use camera to scan QR codes for check-in
- **All Tickets Tab**: View complete ticket database with status
- QR decoding automatically finds ticket and updates status to "Checked In"
- Handles duplicate check-ins with warnings

## Tech Stack

- **Python 3.12**: Core language
- **Streamlit**: Web framework
- **Gspread**: Google Sheets API integration
- **OpenCV**: Image processing for QR scanning
- **Pyzbar**: QR code decoding
- **QRCode**: QR generation
- **Pillow**: Image processing

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable Google Sheets API and Google Drive API
4. Create a Service Account:
   - Go to "Credentials" → "Create Credentials" → "Service Account"
   - Fill in details and create
   - Click the service account, go to "Keys" tab
   - Create a new JSON key and download it
5. Copy the downloaded JSON file contents

### 3. Create Google Sheet

1. Create a new Google Sheet
2. Share it with your service account email (found in the JSON file)
3. Copy the sheet URL

### 4. Configure Streamlit Secrets

**On Windows:**
Create or edit: `%APPDATA%\.streamlit\secrets.toml`

**On Linux/Mac:**
Create or edit: `~/.streamlit/secrets.toml`

Use the template below:

```toml
[google_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"

sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
admin_password = "your-secure-admin-password"
```

Replace all `your-*` fields with actual values from your Google Service Account JSON file.

## Running the Application

```bash
streamlit run app.py
```

The application will open at `http://localhost:8501`

## Usage

### Booking Mode

1. Open `/booking`
2. Enter your name, email, and phone number
3. Select the number of tickets
4. Pay the updated total amount through the UPI QR code
5. Enter your UTR/Transaction ID and submit
6. Check your email and WhatsApp for the ticket QR codes

### Admin Mode

1. Open `/admin`
2. Enter the admin password
3. Use the three tabs:
   - **Approve Tickets**: Review pending bookings and approve them
   - **Scan QR**: Use camera to scan attendee QR codes at entry
   - **All Tickets**: View all ticket data

## Database Schema (Google Sheets)

| Column | Type | Description |
|--------|------|-------------|
| Timestamp | String | Booking creation time (YYYY-MM-DD HH:MM:SS) |
| Name | String | Attendee full name |
| Email | String | Attendee email address |
| Phone | String | Attendee phone number |
| UTR_ID | String | Payment transaction ID |
| UUID | String | Unique ticket identifier |
| Status | String | Ticket status: Pending, Valid, Checked In |
| Booking_ID | String | Shared ID linking tickets from the same booking |
| Ticket_Number | Number | Ticket number within the booking |
| Ticket_Count | Number | Total tickets in the booking |
| Total_Amount | String | Total payment amount for the booking |

## Ticket Status Flow

```
New Booking → Pending → (Admin Approval) → Valid → (Check-in Scan) → Checked In
```

## File Structure

```
.
├── app.py                    # Main Streamlit application
├── sheets_helper.py          # Google Sheets connection and operations
├── qr_helper.py              # QR code generation
├── requirements.txt          # Python dependencies
├── secrets_template.toml     # Template for Streamlit secrets
└── README.md                 # This file
```

## Configuration Options

Edit these in your `secrets.toml`:

- `admin_password`: Change the admin panel password
- `sheet_url`: Update this if using a different Google Sheet
- `google_service_account`: Replace with your service account credentials
- `ticket_amount`, `upi_id`, `merchant_name`: Configure ticket pricing and UPI payment QR
- `smtp_*`: Configure email ticket delivery
- `whatsapp_*`: Configure WhatsApp Cloud API ticket delivery

## Security Notes

⚠️ **Important Security Considerations:**

1. Never commit `secrets.toml` to version control
2. Use strong, unique admin passwords
3. Restrict Google Sheet sharing only to necessary service accounts
4. Regularly audit access logs in Google Cloud Console
5. Consider implementing two-factor authentication for admin access in production

## Troubleshooting

### "Credentials not found in secrets"
- Ensure `secrets.toml` is properly configured
- Verify file location:
  - Windows: `%APPDATA%\.streamlit\secrets.toml`
  - Linux/Mac: `~/.streamlit/secrets.toml`

### "Sheet URL not found"
- Add `sheet_url` to your `secrets.toml`
- Verify the URL format

### QR Scanning not working
- Ensure camera permissions are granted to Streamlit
- Check lighting conditions for QR codes
- Verify QR codes are clearly printed/displayed

### Google Sheets connection fails
- Verify service account has access to the sheet
- Check that Sheet is shared with service account email
- Validate private key formatting (should have `\n` for line breaks)

## Future Enhancements

- Email confirmation system
- Multiple event support
- Advanced analytics dashboard
- Refund management
- Batch QR code generation
- CSV export functionality
- Dark mode support

## License

MIT License - Feel free to use and modify for your needs.

## Support

For issues or questions, please contact the development team or open an issue in the repository.

---

**Built with ❤️ for The Notebook Concert**
