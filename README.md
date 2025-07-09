# Email Forwarder

Python script that manages church newsletter distribution with bidirectional email forwarding and automatic status reporting.

## How It Works

The script monitors `brev@sodertornkyrkan.se` and provides intelligent email forwarding:

1. **Newsletter Distribution**: Forwards emails from admin to active church members (with subject filtering)
2. **Subscriber Feedback**: Forwards emails from members to admin  
3. **Status Reporting**: Automatically notifies admin of delivery success/failures

## Features

- ✅ **Subject filtering**: Only forwards emails containing "församlingsbrev"
- ✅ **Member database integration**: Automatically loads active members from church database
- ✅ **Smart filtering**: Only emails active adult members with valid email addresses
- ✅ **Bidirectional forwarding**: Admin ↔ Members
- ✅ **Automatic status reports** to admin after newsletter distribution
- ✅ **Environment variable support**: Secure password management with .env files
- ✅ **Persistent IMAP/SMTP connections** for better performance
- ✅ **Smart CSV reloading** (only when file changes)
- ✅ **Graceful shutdown** with Ctrl+C
- ✅ **Swedish character support** (ÅÄÖ)
- ✅ **Attachment forwarding** (PDFs, images, etc.)
- ✅ **HTML and plain text** email support

## Email Flow

### Newsletter Distribution (Admin → Members)
```
mattias.michelin@gmail.com
    ↓ (sends email with subject containing "församlingsbrev")
brev@sodertornkyrkan.se 
    ↓ (script processes & forwards)
All active adult members from database
    ↓ (automatic status report)
mattias.michelin@gmail.com (receives "Everything worked!" or failure details)
```

### Member Feedback (Members → Admin)  
```
Any active member from database
    ↓ (sends email)
brev@sodertornkyrkan.se
    ↓ (script forwards with [FROM SUBSCRIBER] prefix)
mattias.michelin@gmail.com
```

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables
Create a `.env` file in the project directory:
```env
PASSWORD=yourpassword
```

**Important**: Never commit the `.env` file to version control! Add it to your `.gitignore`:
```gitignore
.env
```

### 3. Setup Configuration
The script is pre-configured for Södertörnkyrkan:
```python
IMAP_HOST = "mail.sodertornkyrkan.se"
SMTP_HOST = "mail.sodertornkyrkan.se"  
EMAIL = "brev@sodertornkyrkan.se"
PASSWORD = os.getenv("PASSWORD")  # Loaded from .env file
ADMIN_EMAIL = "mattias.michelin@gmail.com"
SUBSCRIBERS_FILE = "sodertornkyrkan-members.csv"
```

### 4. Member Database
The script automatically loads active members from `sodertornkyrkan-members.csv` with these criteria:
- **Status**: "active"
- **Membership**: "member" 
- **Child**: "false" (adults only)
- **Home Email**: must have a valid email address

No manual subscriber list management needed!

### 5. Run the Script
```bash
python email_forwarder.py
```

### 6. Send Newsletter
Send email from `mattias.michelin@gmail.com` to `brev@sodertornkyrkan.se` with subject containing "församlingsbrev"

### 7. Stop the Script
Press `Ctrl+C` for graceful shutdown

## Project Structure
```
├── email_forwarder.py              # Main script
├── sodertornkyrkan-members.csv     # Church member database
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (PASSWORD)
├── .gitignore                     # Git ignore file
└── README.md                      # This file
```

## Subject Filtering

**Only emails with subjects containing "församlingsbrev" get forwarded to members:**

✅ "Församlingsbrev Juli 2024" → **Forwarded**  
✅ "Viktigt meddelande - församlingsbrev" → **Forwarded**  
❌ "Hej, hur mår du?" → **Ignored**  

## Member Database Filtering

The script automatically filters the member database to include only:

| Criteria | Value | Purpose |
|----------|--------|---------|
| Status | "active" | Only current members |
| Membership | "member" | Full members only |
| Child | "false" | Adults only |
| Home Email | Valid email | Must have contact info |

This ensures newsletters only go to active adult members with email addresses.

## Automatic Status Reports

After newsletter distribution, admin receives:

**Success:**
```
Subject: Newsletter Status: Församlingsbrev Juli 2024
Everything worked! Newsletter 'Församlingsbrev Juli 2024' successfully sent to all 45 active members with emails from CSV.
```

**Partial failure:**
```
Subject: Newsletter Status: Församlingsbrev Juli 2024  
Newsletter 'Församlingsbrev Juli 2024' sent to 43/45 active members with emails from CSV.

Failed to send to:
problematic@email.com
invalid@domain.org
```

## Dependencies
- Python 3.6+
- python-dotenv (for environment variable management)

## Security Notes
- ✅ **Password stored in .env file** (not hardcoded in script)
- ✅ **Environment variables** loaded automatically

## Notes
- Script checks for new emails every 10 seconds
- Updates member list automatically when CSV file changes
- Supports Swedish characters (ÅÄÖ) in all content
- Forwards all email types: text, HTML, and attachments
- Provides detailed logging of all operations
- Member count shown on startup and in status reports 