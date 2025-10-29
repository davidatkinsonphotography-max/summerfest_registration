import gspread
from google.oauth2.service_account import Credentials
from django.conf import settings
import os
from threading import Lock

# Thread lock to prevent concurrent writes
write_lock = Lock()

# Google Sheets configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SPREADSHEET_ID = '1bHhv-1x6jQA5XmWi06ujdTtSPk9xzpqqaN3YEM0Y7Ds'
SHEET_NAME = 'Sheet1'  # Change if your sheet has a different name

def get_sheets_client():
    """Initialize and return authenticated Google Sheets client"""
    # Path to your service account JSON file
    json_path = os.path.join(settings.BASE_DIR, 'summerfest-labels-145ab965b7b2.json')
    
    # Authenticate
    creds = Credentials.from_service_account_file(json_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    return client

def append_child_to_sheet(child):
    """
    Append a child's information to the Google Sheet when they check in.
    This function is thread-safe and handles concurrent writes.
    
    Args:
        child: Child model instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Use lock to prevent concurrent writes
    with write_lock:
        try:
            # Get authenticated client
            client = get_sheets_client()
            
            # Open the spreadsheet
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            worksheet = spreadsheet.worksheet(SHEET_NAME)
            
            # Prepare row data
            row_data = [
                child.first_name,
                child.last_name,
                child.get_child_class_display(),  # Full class name like "Minis - School Years 1-2 (2026)"
                'Yes' if child.has_dietary_needs else 'No',
                'Yes' if child.has_medical_needs else 'No',
                'Yes' if child.photo_consent else 'No',
                'No'  # printed field - default to "No"
            ]
            
            # Append the row
            worksheet.append_row(row_data, value_input_option='RAW')
            
            print(f"Successfully appended {child.first_name} {child.last_name} to Google Sheet")
            return True
            
        except Exception as e:
            print(f"Error appending child {child.id} to Google Sheet: {str(e)}")
            # Don't raise the exception - we don't want to block check-in if Google Sheets fails
            return False

def initialize_sheet_headers():
    """
    Initialize the Google Sheet with proper headers.
    Run this once to set up your sheet.
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        
        # Check if headers already exist
        existing_headers = worksheet.row_values(1)
        if existing_headers:
            print("Headers already exist")
            return True
        
        # Add headers
        headers = [
            'Child_First_Name',
            'Child_Last_Name',
            'Child_Class',
            'Has_Dietary_Needs',
            'Has_Medical_Needs',
            'Photo_Consent',
            'Printed'
        ]
        
        worksheet.append_row(headers, value_input_option='RAW')
        print("Headers initialized successfully")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error initializing headers: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return False