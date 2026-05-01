import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from typing import List, Dict, Optional
import json

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_sheets_client():
    """Initialize and cache the Google Sheets client using Streamlit Secrets."""
    try:
        creds_dict = st.secrets["google_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(credentials)
        return client
    except KeyError:
        st.error("Google Service Account credentials not found in secrets. Please configure st.secrets.")
        return None
    except Exception as e:
        error_msg = str(e)
        if "Google Sheets API" in error_msg and "not been used" in error_msg:
            st.error("❌ Google Sheets API is not enabled in your Google Cloud project.\n\nEnable it here: https://console.developers.google.com/apis/api/sheets.googleapis.com/overview")
        else:
            st.error(f"Failed to authenticate with Google Sheets: {error_msg}")
        return None

def get_worksheet(sheet_url: str) -> Optional[gspread.Worksheet]:
    """Get the first worksheet from a Google Sheet URL."""
    client = get_sheets_client()
    if not client:
        return None
    
    try:
        # Clean URL to ensure compatibility
        if "?usp=" in sheet_url:
            sheet_url = sheet_url.split("?")[0]
        
        spreadsheet = client.open_by_url(sheet_url)
        return spreadsheet.sheet1
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg or "404" in error_msg:
            st.error(f"Google Sheet not found. Check that the sheet URL is correct: {sheet_url}")
        else:
            st.error(f"Failed to open worksheet: {error_msg}")
        return None

def initialize_sheet(worksheet: gspread.Worksheet) -> bool:
    """Initialize the worksheet with headers if empty."""
    try:
        headers = [
            "Timestamp",
            "Name",
            "Email",
            "Phone",
            "UTR_ID",
            "UUID",
            "Status",
            "Booking_ID",
            "Ticket_Number",
            "Ticket_Count",
            "Total_Amount",
        ]
        if not worksheet.get_values():
            worksheet.insert_row(headers, 1)
            return True
        
        existing_headers = worksheet.row_values(1)
        missing_headers = [header for header in headers if header not in existing_headers]
        if missing_headers:
            start_col = len(existing_headers) + 1
            for offset, header in enumerate(missing_headers):
                worksheet.update_cell(1, start_col + offset, header)
        return True
    except Exception as e:
        st.error(f"Failed to initialize sheet: {str(e)}")
        return False

def add_ticket(worksheet: gspread.Worksheet, timestamp: str, name: str, email: str, 
               phone: str, utr_id: str, uuid: str, booking_id: str = "",
               ticket_number: int = 1, ticket_count: int = 1,
               total_amount: str = "") -> bool:
    """Add a new ticket to the worksheet."""
    try:
        row = [
            timestamp,
            name,
            email,
            phone,
            utr_id,
            uuid,
            "Pending",
            booking_id,
            ticket_number,
            ticket_count,
            total_amount,
        ]
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to add ticket: {str(e)}")
        return False

def get_all_tickets(worksheet: gspread.Worksheet) -> List[Dict[str, str]]:
    """Retrieve all tickets from the worksheet."""
    try:
        values = worksheet.get_all_values()
        if not values or len(values) < 2:
            return []
        
        headers = values[0]
        tickets = []
        for row in values[1:]:
            ticket = {}
            for i, header in enumerate(headers):
                ticket[header] = row[i] if i < len(row) else ""
            tickets.append(ticket)
        return tickets
    except Exception as e:
        st.error(f"Failed to retrieve tickets: {str(e)}")
        return []

def get_pending_tickets(worksheet: gspread.Worksheet) -> List[Dict[str, str]]:
    """Get all tickets with 'Pending' status."""
    all_tickets = get_all_tickets(worksheet)
    return [ticket for ticket in all_tickets if ticket.get("Status") == "Pending"]

def update_ticket_status(worksheet: gspread.Worksheet, uuid: str, new_status: str) -> bool:
    """Update the status of a ticket by UUID."""
    try:
        values = worksheet.get_all_values()
        headers = values[0]
        uuid_index = headers.index("UUID") + 1
        status_index = headers.index("Status") + 1
        
        for i, row in enumerate(values[1:], start=2):
            if row[headers.index("UUID")] == uuid:
                worksheet.update_cell(i, status_index, new_status)
                return True
        
        return False
    except Exception as e:
        st.error(f"Failed to update ticket status: {str(e)}")
        return False

def find_ticket_by_uuid(worksheet: gspread.Worksheet, uuid: str) -> Optional[Dict[str, str]]:
    """Find a ticket by UUID."""
    all_tickets = get_all_tickets(worksheet)
    for ticket in all_tickets:
        if ticket.get("UUID") == uuid:
            return ticket
    return None
